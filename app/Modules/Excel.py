import datetime as dt
from io import BytesIO
import warnings
warnings.simplefilter("ignore", UserWarning)

import pandas as pd  # noqa


def make_xlsx(df: pd.DataFrame, hotspot_name: str) -> tuple[BytesIO, str, str]:
    """
    :return: BytesIO file, filename, connection_count
    """
    filename = _get_filename(df, hotspot_name)
    connection_count = _rus_connection_count(len(df))

    df = _prepare_data(df, hotspot_name)

    file = BytesIO()
    writer = pd.ExcelWriter(file, engine='xlsxwriter', datetime_format='dd/mm/yy hh:mm')
    df.to_excel(writer, sheet_name='Freewifi', index=False, freeze_panes=(1, 0), header=False, startrow=1)
    _format_excel(df, writer, connection_count)
    file.seek(0)

    return file, filename, connection_count


def _prepare_data(df: pd.DataFrame, hotspot_name: str) -> pd.DataFrame:
    df['hotspot'] = hotspot_name

    df['acctinputoctets'] = df['acctinputoctets'].div(1000000).round(2)
    df['acctoutputoctets'] = df['acctoutputoctets'].div(1000000).round(2)

    # Replace erroneous durations > 24h with None
    df['acctsessiontime'] = df['acctsessiontime'].apply(
        lambda x: None if x >= 86400 else x
    )

    column_names = {'hotspot': 'Точка',
                    'mac': 'MAC-адрес',
                    'phone': 'Телефон',
                    'acctstarttime': 'Подключение',
                    'acctsessiontime': 'Длительность (час:мин)',
                    'acctoutputoctets': 'Принято Мегабайт',
                    'acctinputoctets': 'Передано Мегабайт'}
    df = df[column_names.keys()]
    df = df.rename(columns=column_names)

    return df


def _format_excel(df: pd.DataFrame, writer: pd.ExcelWriter, connection_count: str):
    workbook = writer.book  # noqa
    worksheet = writer.sheets['Freewifi']
    worksheet.set_column("A:Z", 20)
    worksheet.set_default_row(25)
    worksheet.autofilter(0, 0, 0, 6)

    header = {'bold': True, 'valign': 'vcenter', 'align': 'center',
              'fg_color': '#E7652B', 'font_color': 'white', 'border': 1}
    header_format = workbook.add_format(header)
    for col_num, value in enumerate(df.columns.values):
        worksheet.write(0, col_num, value, header_format)

    duration_format = workbook.add_format({'num_format': "[h]:mm"})
    row = 1
    for value in df['Длительность (час:мин)'].values:
        try:
            worksheet.write(row, 4, pd.to_timedelta(value, unit='s'), duration_format)
        except ValueError:
            worksheet.write(row, 4, '')
        except Exception as e:
            print(e)
        row += 1

    # Totals
    total_format = workbook.add_format({'bold': True, 'top': 3, 'num_format': '#,###'})
    total_duration = pd.to_timedelta(df['Длительность (час:мин)'], unit='s').sum(skipna=True)
    total_duration_format = workbook.add_format({'num_format': "[h]:mm", 'bold': True, 'top': 3})
    blank_format = workbook.add_format({'bold': True, 'top': 3, 'font_color': 'white'})

    worksheet.write(f'A{row+1}', connection_count, total_format)
    worksheet.write(f'B{row+1}', '', total_format)
    worksheet.write(f'C{row+1}', '', total_format)
    worksheet.write(f'D{row+1}', f'=SUBTOTAL(2, D1:D{row})', blank_format)  # Pseudo-SUBTOT. to exclude row from filter
    worksheet.write(f'E{row+1}', total_duration, total_duration_format)  # Can't use SUBTOT9 because of iPhones
    worksheet.write(f'F{row+1}', df["Принято Мегабайт"].sum(), total_format)
    worksheet.write(f'G{row+1}', df["Передано Мегабайт"].sum(), total_format)

    writer.save()


def _rus_connection_count(n: int) -> str:
    if str(n).endswith(('5', '6', '7', '8', '9', '0', '11', '12', '13', '14')):
        connections = 'подключений'
    elif str(n).endswith('1'):
        connections = 'подключение'
    else:
        connections = 'подключения'
    return f'{n:,} {connections}'


def _get_filename(df: pd.DataFrame, hotspot_name: str) -> str:
    extension = ".xlsx"
    mindate = df.acctstarttime.min().date()
    maxdate = df.acctstarttime.max().date()
    hotspot_name = hotspot_name[:40]  # tg filename limit is 60
    if mindate == maxdate:
        filename = f'{hotspot_name}-{mindate:%d.%m.%y}'
    else:
        filename = f'{hotspot_name}-{mindate:%d.%m.%y}_{maxdate:%d.%m.%y}'
    if maxdate == dt.date.today():
        filename += '_'

    return filename + extension
