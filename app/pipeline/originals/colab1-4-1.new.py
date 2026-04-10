import pandas as pd
import os
import openpyxl  # 追加
from IPython.display import display, HTML

file_path = '/content/CF付財務分析表（経営指標あり）_Claude_Ver.xlsx'
sheet_name = 'CF計算書'

if not os.path.exists(file_path):
    print(f"エラー: ファイルが見つかりません。パスを確認してください: {file_path}")
else:
    try:
        # 【修正ポイント】 openpyxlを使って「データのみ」でロードする
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb[sheet_name]

        # openpyxlのワークシートをPandasのDataFrameに変換
        data = ws.values
        columns = next(data) # 最初の行をカラムにする（今回は後で無視するので形式的）
        df_raw = pd.DataFrame(data)

        # 不要な1-4行目(index 0-3)と52行目(index 51)を削除
        # B5(1,1), C6(2,2) などの座標からヘッダー情報を取得
        header_info_period = df_raw.iloc[4, 1]
        header_info_unit = df_raw.iloc[5, 2]

        # テーブル用データは7行目(index 6)から51行目(index 50)まで
        df = df_raw.iloc[6:51, [1, 2]].fillna('')

        custom_css = """
        <style>
            .report-container { font-family: "Meiryo", sans-serif; color: #000; }
            .report-title { font-size: 18px; font-weight: bold; margin: 20px 0 5px 0; border-left: 5px solid #000; padding-left: 10px; }
            .report-meta { font-size: 13px; margin-bottom: 5px; display: flex; justify-content: space-between; width: 580px; }
            .excel-table {
                border-collapse: collapse; width: fit-content; display: inline-table; font-size: 13px;
                table-layout: fixed; outline: 2px solid #000; box-shadow: 0 0 0 2px #000; background-color: white;
            }
            .excel-table td {
                border-left: 1px solid #999; border-bottom: 1px solid #999;
                padding: 4px 10px; overflow: hidden; white-space: nowrap; box-sizing: border-box; color: #000;
            }
            .excel-table tr td:last-child { border-right: 1px solid #999; }
            .col-subject { width: 400px; text-align: left; }
            .col-amt { width: 180px; text-align: right; font-family: "Consolas", monospace; }
            .header-row td { background-color: #004080 !important; color: #ffffff !important; font-weight: bold; }
            .total-row { background-color: #e6f3ff !important; font-weight: bold; }
            .grand-total { background-color: #d9ead3 !important; font-weight: bold; }
        </style>
        """

        html_output = f'<div class="report-container">'
        html_output += f'<div class="report-title">キャッシュ・フロー計算書</div>'
        html_output += f'<div class="report-meta"><span>{header_info_period}</span><span>{header_info_unit}</span></div>'
        html_output += '<table class="excel-table"><tbody>'

        for i, row in df.iterrows():
            content = str(row.iloc[0]).strip()
            if not content and (row.iloc[1] == "" or row.iloc[1] is None): continue

            row_class = ""
            if "キャッシュ・フロー" in content and i < 20: row_class = "header-row"
            elif "計" in content: row_class = "total-row"
            elif "現金及び現金同等物" in content: row_class = "grand-total"

            html_output += f'<tr class="{row_class}"><td class="col-subject">{row.iloc[0]}</td>'

            val = row.iloc[1]
            # 数値変換とカンマ区切り（int型に変換可能な場合のみ）
            try:
                if isinstance(val, (int, float)) and val != "":
                    display_val = "{:,}".format(int(val))
                else:
                    display_val = val if val is not None else ""
            except:
                display_val = val

            html_output += f'<td class="col-amt">{display_val}</td></tr>'

        html_output += '</tbody></table></div>'
        display(HTML(custom_css + html_output))

    except Exception as e:
        print(f"エラー: {e}")