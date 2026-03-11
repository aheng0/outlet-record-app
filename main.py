# 入河排污口现场工作记录App - 终极调试版（分步显示）
import flet as ft
import sqlite3
import json
import csv
import os
import base64
import traceback
from datetime import datetime

# 全局调试信息列表（将在屏幕上显示）
debug_messages = []

def debug_print(page, msg):
    """在屏幕上添加调试信息并更新页面"""
    debug_messages.append(msg)
    if page and page.controls:
        # 如果页面已有控件，直接添加文本
        page.add(ft.Text(msg, size=12, color=ft.colors.BLUE))
    page.update()

# ==================== 数据库操作类 ====================
class Database:
    def __init__(self, page=None):
        self.page = page
        try:
            debug_print(page, "数据库初始化...")
            self.conn = sqlite3.connect('records.db', check_same_thread=False)
            self.create_table()
            debug_print(page, "数据库连接成功")
        except Exception as e:
            debug_print(page, f"数据库错误: {e}")

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                create_time TEXT,
                task_source TEXT,
                outlet_name TEXT,
                outlet_name_status TEXT,
                outlet_code TEXT,
                outlet_code_status TEXT,
                province TEXT, city TEXT, county TEXT, town TEXT, village TEXT,
                longitude REAL, latitude REAL,
                in_national_platform INTEGER,
                water_body TEXT,
                water_func_zone1 TEXT,
                water_func_zone2 TEXT,
                downstream_section TEXT,
                downstream_distance REAL,
                entry_method TEXT,
                outlet_type_main TEXT,
                outlet_type_sub TEXT,
                responsible_party_status TEXT,
                responsible_parties TEXT,
                is_discharging TEXT,
                color_desc TEXT,
                turbidity_desc TEXT,
                odor_desc TEXT,
                has_oil_film TEXT,
                other_issues TEXT,
                photo1 TEXT, photo2 TEXT, photo3 TEXT, photo4 TEXT,
                monitor_status TEXT,
                monitor_unavailable_reason TEXT,
                monitor_people TEXT,
                monitor_start_time TEXT,
                monitor_end_time TEXT,
                flow_status TEXT,
                flow_value REAL,
                water_temp REAL,
                ph_value REAL,
                conductivity REAL,
                quick_cod REAL,
                quick_nh3n REAL,
                quick_tp REAL,
                quick_tn REAL,
                other_index TEXT,
                monitor_photo1 TEXT, monitor_photo2 TEXT, monitor_photo3 TEXT, monitor_photo4 TEXT,
                sample_status TEXT,
                sample_indicators TEXT,
                other_indicators TEXT,
                test_institution TEXT,
                sample_arrive_time TEXT,
                leader TEXT, leader_phone TEXT,
                participants TEXT,
                remark TEXT
            )
        ''')
        self.conn.commit()

    # ... 其他方法保持不变（insert_record, update_record 等）
    def insert_record(self, data):
        cursor = self.conn.cursor()
        columns = ','.join(data.keys())
        placeholders = ','.join(['?' for _ in data])
        sql = f"INSERT INTO records ({columns}) VALUES ({placeholders})"
        cursor.execute(sql, list(data.values()))
        self.conn.commit()
        return cursor.lastrowid

    def update_record(self, record_id, data):
        cursor = self.conn.cursor()
        set_clause = ', '.join([f"{col}=?" for col in data.keys()])
        sql = f"UPDATE records SET {set_clause} WHERE id=?"
        cursor.execute(sql, list(data.values()) + [record_id])
        self.conn.commit()

    def get_all_records(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, create_time, outlet_name FROM records ORDER BY create_time DESC")
        return cursor.fetchall()

    def get_record_by_id(self, record_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM records WHERE id = ?", (record_id,))
        columns = [description[0] for description in cursor.description]
        record = cursor.fetchone()
        if record:
            return dict(zip(columns, record))
        return None

    def delete_record(self, record_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM records WHERE id = ?", (record_id,))
        self.conn.commit()

# ==================== 导出工具函数 ====================
def image_to_base64(image_path):
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, 'rb') as f:
            img_bytes = f.read()
        return base64.b64encode(img_bytes).decode('utf-8')
    except:
        return None

def status_to_chinese(value, mapping):
    return mapping.get(value, value)

def export_to_word(record_id, page):
    db = Database()
    record = db.get_record_by_id(record_id)
    if not record:
        page.show_snack_bar(ft.SnackBar(content=ft.Text("记录不存在")))
        return

    def checkbox_if(condition):
        return "☑" if condition else ""

    task_source = record.get('task_source', '')
    if task_source.startswith('其他:'):
        task_source_display = '其他工作：' + task_source[3:]
    else:
        task_source_display = task_source

    name_status = record.get('outlet_name_status', 'unknown')
    name_val = record.get('outlet_name', '')
    if name_status == 'known':
        name_display = f"已掌握：{name_val}"
    elif name_status == 'sign':
        name_display = f"现场标识牌显示：{name_val}"
    else:
        name_display = "暂不掌握"

    code_status = record.get('outlet_code_status', 'unknown')
    code_val = record.get('outlet_code', '')
    if code_status == 'known':
        code_display = f"已掌握：{code_val}"
    elif code_status == 'sign':
        code_display = f"现场标识牌显示：{code_val}"
    else:
        code_display = "暂不掌握"

    platform = record.get('in_national_platform', 0)
    if platform == 1:
        platform_display = "☑ 是"
    elif platform == 2:
        platform_display = "☑ 需进一步核实"
    else:
        platform_display = "☑ 否"

    responsible_status = record.get('responsible_party_status', 'unknown')
    responsible_parties = []
    try:
        parties = json.loads(record.get('responsible_parties', '[]'))
        for p in parties:
            responsible_parties.append(f"{p.get('name','')}（{p.get('industry','')}）")
    except:
        pass
    if responsible_status == 'known':
        responsible_display = "已确定：" + ('；'.join(responsible_parties) if responsible_parties else '')
    else:
        responsible_display = "暂无法确定，需进一步溯源"

    discharging = record.get('is_discharging', '否')
    discharging_display = f"☑ {discharging}" if discharging == '是' else "☑ 否"

    oil = record.get('has_oil_film', '无')
    oil_display = f"☑ {oil}" if oil == '有' else "☑ 无"

    monitor_status = record.get('monitor_status', 'no')
    if monitor_status == 'yes':
        monitor_display = "☑ 是"
    elif monitor_status == 'unavailable':
        monitor_display = "☑ 不具备条件：" + record.get('monitor_unavailable_reason', '')
    else:
        monitor_display = "☑ 否"

    flow_status = record.get('flow_status', 'unmeasured')
    if flow_status == 'measured':
        flow_display = f"☑ 现场测定：{record.get('flow_value', '')} m³/s"
    elif flow_status == 'unavailable':
        flow_display = "☑ 不具备测定条件"
    else:
        flow_display = "☑ 未测定"

    sample_status = record.get('sample_status', 'no')
    sample_display = "☑ 是" if sample_status == 'yes' else "☑ 否"

    def photo_cell(photo_field, caption):
        path = record.get(photo_field, '')
        b64 = image_to_base64(path)
        if b64:
            img_html = f'<img src="data:image/jpeg;base64,{b64}" style="max-width:6cm; max-height:6cm; width:auto; height:auto; object-fit:contain;"/>'
        else:
            img_html = '（未拍摄）'
        return f'<div style="text-align:center;"><div>{img_html}</div><div style="font-size:small;">{caption}</div></div>'

    def photo_grid(prefix, captions):
        cells = []
        for i in range(4):
            cells.append(f'<td style="width:50%; border:1px solid black; padding:5px;">{photo_cell(f"{prefix}{i+1}", captions[i])}</td>')
        return f'''
            <table style="width:100%; border-collapse:collapse;">
                <tr>{cells[0]}{cells[1]}</tr>
                <tr>{cells[2]}{cells[3]}</tr>
            </table>
        '''

    general_captions = ["排污口近景照片1", "排污口近景照片2", "排污口标识牌照片", "排污口远景照片"]
    monitor_captions = ["监测采样点照片（展示测流及采样条件）", "采样或测流工作照片", "水样照片（可准确显示水样颜色和浑浊程度）", "快检结果照片（各指标合拍）"]

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>入河排污口现场工作记录单</title>
        <style>
            body {{ font-family: SimSun, '宋体', serif; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid black; padding: 8px; vertical-align: top; }}
            .first-col {{ width: 3cm; }}
        </style>
    </head>
    <body>
        <h2 style="text-align:center;">入河排污口现场工作记录单</h2>
        <table>
            <tr><td class="first-col">任务来源</td><td>{task_source_display}</td></tr>
            <tr><td>排污口名称</td><td>{name_display}</td></tr>
            <tr><td>排污口编码</td><td>{code_display}</td></tr>
            <tr><td>纳入国家平台</td><td>{platform_display}</td></tr>
            <tr><td>排污口位置</td><td>
                所在行政区域：{record.get('province','')} {record.get('city','')} {record.get('county','')} {record.get('town','')} {record.get('village','')}<br>
                排入水体名称：{record.get('water_body','')}<br>
                一级水功能区名称：{record.get('water_func_zone1','')}<br>
                二级水功能区名称：{record.get('water_func_zone2','')}<br>
                下游最近国控断面名称：{record.get('downstream_section','')} 距离：{record.get('downstream_distance','')} km<br>
                东经：{record.get('longitude',0):.6f} 度；北纬：{record.get('latitude',0):.6f} 度
            </td></tr>
            <tr><td>污水入河方式</td><td>{record.get('entry_method','')}</td></tr>
            <tr><td>排污口类型</td><td>
                一级分类：{record.get('outlet_type_main','')}<br>
                二级分类/具体情况：{record.get('outlet_type_sub','')}
            </td></tr>
            <tr><td>责任主体情况</td><td>{responsible_display}</td></tr>
            <tr><td>现场情况</td><td>
                正在排放污水：{discharging_display}<br>
                感官描述：颜色 {record.get('color_desc','')}；浑浊度 {record.get('turbidity_desc','')}；气味 {record.get('odor_desc','')}<br>
                水面有无油膜：{oil_display}<br>
                其他问题：{record.get('other_issues','')}
            </td></tr>
            <tr><td>现场照片</td><td>{photo_grid('photo', general_captions)}</td></tr>
            <tr><td>现场监测</td><td>
                {monitor_display}<br>
                监测人员：{', '.join(json.loads(record.get('monitor_people','[]')))}<br>
                监测时间：{record.get('monitor_start_time','')} 至 {record.get('monitor_end_time','')}<br>
                流量：{flow_display}<br>
                水温：{record.get('water_temp','')} ℃；pH值：{record.get('ph_value','')}；电导率：{record.get('conductivity','')} μs/cm<br>
                快检结果：COD {record.get('quick_cod','')} mg/L，氨氮 {record.get('quick_nh3n','')} mg/L，总磷 {record.get('quick_tp','')} mg/L，总氮 {record.get('quick_tn','')} mg/L<br>
                其他指标：{record.get('other_index','')}<br>
                监测现场照片：{photo_grid('monitor_photo', monitor_captions)}
            </td></tr>
            <tr><td>采样送检</td><td>
                {sample_display}<br>
                送检指标：{', '.join(json.loads(record.get('sample_indicators','[]')))}<br>
                其他选测指标：{record.get('other_indicators','')}<br>
                检测机构：{record.get('test_institution','')}<br>
                样品送达时间：{record.get('sample_arrive_time','')}
            </td></tr>
            <tr><td>现场工作人员</td><td>
                负责人：{record.get('leader','')} 联系电话：{record.get('leader_phone','')}<br>
                参加人员：{', '.join(json.loads(record.get('participants','[]')))}
            </td></tr>
            <tr><td>备注</td><td>{record.get('remark','')}</td></tr>
        </table>
    </body>
    </html>
    """

    filename = f"排污口记录_{record_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.doc"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)
    page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Word已导出: {filename}")))

def export_to_excel(db, page):
    cursor = db.conn.cursor()
    cursor.execute("SELECT * FROM records")
    rows = cursor.fetchall()
    col_names = [description[0] for description in cursor.description]

    def safe_json_loads(val):
        try:
            return json.loads(val) if val else []
        except:
            return []

    column_config = [
        ("ID", lambda row: row[0]),
        ("创建时间", lambda row: row[1]),
        ("排污口名称掌握状态", lambda row: status_to_chinese(row[col_names.index('outlet_name_status')],
                        {'unknown':'暂不掌握','known':'已掌握','sign':'现场标识牌显示'})),
        ("排污口名称", lambda row: row[col_names.index('outlet_name')]),
        ("排污口编码掌握状态", lambda row: status_to_chinese(row[col_names.index('outlet_code_status')],
                        {'unknown':'暂不掌握','known':'已掌握','sign':'现场标识牌显示'})),
        ("排污口编码", lambda row: row[col_names.index('outlet_code')]),
        ("省（区）", lambda row: row[col_names.index('province')]),
        ("市（州、盟）", lambda row: row[col_names.index('city')]),
        ("县（区、旗、市）", lambda row: row[col_names.index('county')]),
        ("乡（镇、街道）", lambda row: row[col_names.index('town')]),
        ("村（社区）", lambda row: row[col_names.index('village')]),
        ("经度", lambda row: f"{row[col_names.index('longitude')]:.6f}" if row[col_names.index('longitude')] else ""),
        ("纬度", lambda row: f"{row[col_names.index('latitude')]:.6f}" if row[col_names.index('latitude')] else ""),
        ("纳入国家平台", lambda row: status_to_chinese(str(row[col_names.index('in_national_platform')]),
                        {'0':'否','1':'是','2':'需进一步核实'})),
        ("排入水体名称", lambda row: row[col_names.index('water_body')]),
        ("一级水功能区名称", lambda row: row[col_names.index('water_func_zone1')]),
        ("二级水功能区名称", lambda row: row[col_names.index('water_func_zone2')]),
        ("下游最近国控断面名称", lambda row: row[col_names.index('downstream_section')]),
        ("距离(km)", lambda row: row[col_names.index('downstream_distance')]),
        ("入河方式", lambda row: row[col_names.index('entry_method')]),
        ("排污口一级分类", lambda row: row[col_names.index('outlet_type_main')]),
        ("排污口二级分类", lambda row: row[col_names.index('outlet_type_sub')]),
        ("责任主体是否确定", lambda row: status_to_chinese(row[col_names.index('responsible_party_status')],
                        {'unknown':'否','known':'是'})),
        ("责任主体名称", lambda row: (lambda parties: parties[0].get('name','') if parties else '')(safe_json_loads(row[col_names.index('responsible_parties')]))),
        ("行业类别", lambda row: (lambda parties: parties[0].get('industry','') if parties else '')(safe_json_loads(row[col_names.index('responsible_parties')]))),
        ("其他责任主体名称及类别", lambda row: (lambda parties: '；'.join([f"{p.get('name','')}({p.get('industry','')})" for p in parties[1:]]) if len(parties)>1 else '')(safe_json_loads(row[col_names.index('responsible_parties')]))),
        ("是否排放污水", lambda row: row[col_names.index('is_discharging')]),
        ("颜色", lambda row: row[col_names.index('color_desc')]),
        ("浑浊度", lambda row: row[col_names.index('turbidity_desc')]),
        ("气味", lambda row: row[col_names.index('odor_desc')]),
        ("有无油膜", lambda row: row[col_names.index('has_oil_film')]),
        ("其他问题", lambda row: row[col_names.index('other_issues')]),
        ("照片1", lambda row: os.path.basename(row[col_names.index('photo1')]) if row[col_names.index('photo1')] else ""),
        ("照片2", lambda row: os.path.basename(row[col_names.index('photo2')]) if row[col_names.index('photo2')] else ""),
        ("照片3", lambda row: os.path.basename(row[col_names.index('photo3')]) if row[col_names.index('photo3')] else ""),
        ("照片4", lambda row: os.path.basename(row[col_names.index('photo4')]) if row[col_names.index('photo4')] else ""),
        ("监测状态", lambda row: status_to_chinese(row[col_names.index('monitor_status')],
                        {'yes':'是','no':'否','unavailable':'不具备条件'})),
        ("监测不具备条件原因", lambda row: row[col_names.index('monitor_unavailable_reason')]),
        ("监测人员", lambda row: ', '.join(safe_json_loads(row[col_names.index('monitor_people')]))),
        ("监测开始时间", lambda row: row[col_names.index('monitor_start_time')]),
        ("监测结束时间", lambda row: row[col_names.index('monitor_end_time')]),
        ("流量测定状态", lambda row: status_to_chinese(row[col_names.index('flow_status')],
                        {'unavailable':'不具备测定条件','unmeasured':'未测定','measured':'现场测定'})),
        ("流量值", lambda row: row[col_names.index('flow_value')]),
        ("水温(℃)", lambda row: row[col_names.index('water_temp')]),
        ("pH值", lambda row: row[col_names.index('ph_value')]),
        ("电导率(μs/cm)", lambda row: row[col_names.index('conductivity')]),
        ("COD快检(mg/L)", lambda row: row[col_names.index('quick_cod')]),
        ("氨氮快检(mg/L)", lambda row: row[col_names.index('quick_nh3n')]),
        ("总磷快检(mg/L)", lambda row: row[col_names.index('quick_tp')]),
        ("总氮快检(mg/L)", lambda row: row[col_names.index('quick_tn')]),
        ("其他指标", lambda row: row[col_names.index('other_index')]),
        ("监测照片1", lambda row: os.path.basename(row[col_names.index('monitor_photo1')]) if row[col_names.index('monitor_photo1')] else ""),
        ("监测照片2", lambda row: os.path.basename(row[col_names.index('monitor_photo2')]) if row[col_names.index('monitor_photo2')] else ""),
        ("监测照片3", lambda row: os.path.basename(row[col_names.index('monitor_photo3')]) if row[col_names.index('monitor_photo3')] else ""),
        ("监测照片4", lambda row: os.path.basename(row[col_names.index('monitor_photo4')]) if row[col_names.index('monitor_photo4')] else ""),
        ("采样送检状态", lambda row: status_to_chinese(row[col_names.index('sample_status')],
                        {'yes':'是','no':'否'})),
        ("送检指标", lambda row: ', '.join(safe_json_loads(row[col_names.index('sample_indicators')]))),
        ("其他选测指标", lambda row: row[col_names.index('other_indicators')]),
        ("检测机构", lambda row: row[col_names.index('test_institution')]),
        ("样品送达时间", lambda row: row[col_names.index('sample_arrive_time')]),
        ("负责人", lambda row: row[col_names.index('leader')]),
        ("负责人电话", lambda row: row[col_names.index('leader_phone')]),
        ("参加人员", lambda row: ', '.join(safe_json_loads(row[col_names.index('participants')]))),
        ("备注", lambda row: row[col_names.index('remark')]),
    ]

    filename = f"排污口台账_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
    filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow([cfg[0] for cfg in column_config])
        for row in rows:
            row_data = [cfg[1](row) for cfg in column_config]
            writer.writerow(row_data)
    page.show_snack_bar(ft.SnackBar(content=ft.Text(f"台账已导出: {filename}")))

# ==================== 主程序 ====================
def main(page: ft.Page):
    # 首先在屏幕上显示调试信息
    page.clean()
    page.add(ft.Text("=== 启动调试信息 ===", size=16, weight=ft.FontWeight.BOLD))
    page.update()

    try:
        debug_print(page, "1. main 函数开始执行")

        page.title = "入河排污口现场记录"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20
        page.scroll = ft.ScrollMode.AUTO
        page.window.width = 400
        page.window.height = 700
        debug_print(page, "2. 页面基本设置完成")

        # 将 page 传递给数据库，以便数据库也能输出调试信息
        debug_print(page, "3. 正在初始化数据库...")
        db = Database(page=page)

        current_edit_id = None
        photo_paths = ["", "", "", ""]
        monitor_photo_paths = ["", "", "", ""]

        debug_print(page, "4. 变量初始化完成")

        # ========== 列表页 ==========
        def show_list_view():
            debug_print(page, "5. show_list_view 被调用")
            page.clean()
            records = db.get_all_records()
            debug_print(page, f"6. 获取到 {len(records)} 条记录")
            record_cards = []
            for record in records:
                record_id, create_time, outlet_name = record
                try:
                    time_str = datetime.fromisoformat(create_time).strftime("%Y-%m-%d %H:%M")
                except:
                    time_str = create_time
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.ASSIGNMENT),
                                title=ft.Text(outlet_name if outlet_name else "未命名记录"),
                                subtitle=ft.Text(f"创建时间: {time_str}"),
                            ),
                            ft.Row([
                                ft.TextButton("查看/编辑", on_click=lambda e, rid=record_id: show_form_view(rid)),
                                ft.TextButton("删除", on_click=lambda e, rid=record_id: delete_record(rid)),
                                ft.TextButton("导出Word", on_click=lambda e, rid=record_id: export_to_word(rid, page)),
                            ], alignment=ft.MainAxisAlignment.END)
                        ]),
                        padding=10,
                    )
                )
                record_cards.append(card)
                debug_print(page, f"7. 添加卡片: {outlet_name}")

            if not record_cards:
                record_cards.append(ft.Text("暂无记录，点击下方+号添加"))

            page.add(
                ft.Row([
                    ft.Text("记录列表", size=24, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.ElevatedButton("导出Excel", on_click=lambda e: export_to_excel(db, page)),
                        ft.IconButton(icon=ft.icons.ADD, icon_size=30, on_click=lambda e: show_form_view(None)),
                    ]),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Column(record_cards, scroll=ft.ScrollMode.AUTO, expand=True),
            )
            page.update()
            debug_print(page, "8. 列表页面渲染完成")

        def delete_record(record_id):
            debug_print(page, f"删除记录 {record_id}")
            db.delete_record(record_id)
            page.show_snack_bar(ft.SnackBar(content=ft.Text("删除成功")))
            show_list_view()

        # ========== 表单页 ==========
        def show_form_view(record_id=None):
            debug_print(page, f"9. show_form_view 被调用，record_id={record_id}")
            page.clean()
            nonlocal current_edit_id, photo_paths, monitor_photo_paths
            current_edit_id = record_id
            photo_paths = ["", "", "", ""]
            monitor_photo_paths = ["", "", "", ""]
            debug_print(page, "10. 表单变量重置")

            record_data = {}
            if record_id:
                record_data = db.get_record_by_id(record_id) or {}
                for i in range(4):
                    photo_paths[i] = record_data.get(f'photo{i+1}', '')
                    monitor_photo_paths[i] = record_data.get(f'monitor_photo{i+1}', '')
                debug_print(page, f"11. 加载编辑数据，照片路径 {photo_paths}")

            # ---------- 工具函数：动态添加行 ----------
            participant_rows = []
            participants_container = ft.Column([])

            def add_participant(e):
                participant_rows.append(ft.TextField(label="参加人员", width=300))
                participants_container.controls = participant_rows
                page.update()
                debug_print(page, "12. 添加参加人员")

            if record_data.get('participants'):
                try:
                    part_list = json.loads(record_data['participants'])
                    for name in part_list:
                        participant_rows.append(ft.TextField(value=name, label="参加人员", width=300))
                    debug_print(page, f"13. 加载已有参加人员 {part_list}")
                except:
                    pass
            participants_container.controls = participant_rows

            # 责任主体动态行
            def create_responsible_row(name="", industry=""):
                return ft.Row([
                    ft.TextField(value=name, label="主体名称", width=200),
                    ft.TextField(value=industry, label="行业类别", width=200),
                ])

            responsible_rows = []
            responsible_container = ft.Column([])

            def add_responsible(e):
                responsible_rows.append(create_responsible_row())
                responsible_container.controls = responsible_rows
                page.update()
                debug_print(page, "14. 添加责任主体")

            if record_data.get('responsible_parties'):
                try:
                    parties = json.loads(record_data['responsible_parties'])
                    for p in parties:
                        responsible_rows.append(create_responsible_row(p.get('name', ''), p.get('industry', '')))
                    debug_print(page, f"15. 加载已有责任主体 {parties}")
                except:
                    pass
            responsible_container.controls = responsible_rows

            # 监测人员动态行
            monitor_people_rows = []
            monitor_people_container = ft.Column([])

            def add_monitor_people(e):
                monitor_people_rows.append(ft.TextField(label="监测人员", width=300))
                monitor_people_container.controls = monitor_people_rows
                page.update()
                debug_print(page, "16. 添加监测人员")

            if record_data.get('monitor_people'):
                try:
                    people_list = json.loads(record_data['monitor_people'])
                    for name in people_list:
                        monitor_people_rows.append(ft.TextField(value=name, label="监测人员", width=300))
                    debug_print(page, f"17. 加载已有监测人员 {people_list}")
                except:
                    pass
            else:
                monitor_people_rows = [ft.TextField(label="监测人员", width=300) for _ in range(2)]
                debug_print(page, "18. 创建默认两个监测人员空行")
            monitor_people_container.controls = monitor_people_rows

            # ---------- 创建表单控件 ----------
            debug_print(page, "19. 开始创建表单控件")

            # 1. 任务来源
            task_source_radio = ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="监督性抽测", label="监督性抽测"),
                    ft.Radio(value="暗查摸排", label="暗查摸排"),
                    ft.Radio(value="监督检查", label="监督检查"),
                    ft.Radio(value="其他", label="其他工作"),
                ]),
                value=record_data.get('task_source', '') if record_data.get('task_source') else ''
            )
            other_task_field = ft.TextField(label="请注明其他工作内容", visible=False, width=300)

            def on_task_source_change(e):
                other_task_field.visible = (task_source_radio.value == "其他")
                page.update()
            task_source_radio.on_change = on_task_source_change

            if record_data.get('task_source', '').startswith("其他:"):
                task_source_radio.value = "其他"
                other_task_field.value = record_data['task_source'][3:]
                other_task_field.visible = True
                debug_print(page, "20. 任务来源加载完成")

            # 2. 排污口名称
            name_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="unknown", label="暂不掌握"),
                    ft.Radio(value="known", label="已掌握"),
                    ft.Radio(value="sign", label="现场标识牌显示"),
                ]),
                value=record_data.get('outlet_name_status', 'unknown')
            )
            outlet_name = ft.TextField(label="排污口名称", value=record_data.get('outlet_name', ''), width=300,
                                       disabled=(record_data.get('outlet_name_status', 'unknown') == 'unknown'))

            def on_name_radio_change(e):
                outlet_name.disabled = (name_radio.value == "unknown")
                if name_radio.value == "unknown":
                    outlet_name.value = ""
                page.update()
            name_radio.on_change = on_name_radio_change
            debug_print(page, "21. 排污口名称控件创建")

            # 3. 排污口编码
            code_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="unknown", label="暂不掌握"),
                    ft.Radio(value="known", label="已掌握"),
                    ft.Radio(value="sign", label="现场标识牌显示"),
                ]),
                value=record_data.get('outlet_code_status', 'unknown')
            )
            outlet_code = ft.TextField(label="排污口编码", value=record_data.get('outlet_code', ''), width=300,
                                       disabled=(record_data.get('outlet_code_status', 'unknown') == 'unknown'))

            def on_code_radio_change(e):
                outlet_code.disabled = (code_radio.value == "unknown")
                if code_radio.value == "unknown":
                    outlet_code.value = ""
                page.update()
            code_radio.on_change = on_code_radio_change
            debug_print(page, "22. 排污口编码控件创建")

            # 4. 纳入国家平台
            platform_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="1", label="是"),
                    ft.Radio(value="0", label="否"),
                    ft.Radio(value="2", label="需进一步核实"),
                ]),
                value=str(record_data.get('in_national_platform', '0'))
            )
            debug_print(page, "23. 国家平台控件创建")

            # 5. 行政区（五级）
            province = ft.TextField(label="省（区）", value=record_data.get('province', ''))
            city = ft.TextField(label="市（州、盟）", value=record_data.get('city', ''))
            county = ft.TextField(label="县（区、旗、市）", value=record_data.get('county', ''))
            town = ft.TextField(label="乡（镇、街道）", value=record_data.get('town', ''))
            village = ft.TextField(label="村（社区）", value=record_data.get('village', ''))
            debug_print(page, "24. 行政区控件创建")

            # 6. 经纬度
            longitude = ft.TextField(label="经度", value=str(record_data.get('longitude', '')))
            latitude = ft.TextField(label="纬度", value=str(record_data.get('latitude', '')))
            def get_location(e):
                longitude.value = "116.397428"
                latitude.value = "39.90923"
                page.update()
            get_location_btn = ft.ElevatedButton("获取当前位置", on_click=get_location)
            debug_print(page, "25. 经纬度控件创建")

            # 7. 水体信息
            water_body = ft.TextField(label="排入水体名称", value=record_data.get('water_body', ''))
            water_func_zone1 = ft.TextField(label="一级水功能区名称", value=record_data.get('water_func_zone1', ''))
            water_func_zone2 = ft.TextField(label="二级水功能区名称", value=record_data.get('water_func_zone2', ''))
            downstream_section = ft.TextField(label="下游最近国控断面名称", value=record_data.get('downstream_section', ''))
            downstream_distance = ft.TextField(label="距离 (km)", value=str(record_data.get('downstream_distance', '')))
            debug_print(page, "26. 水体信息控件创建")

            # 8. 入河方式
            entry_methods = ["明渠", "管道", "泵站", "涵闸", "箱涵", "其他"]
            entry_dropdown = ft.Dropdown(
                label="污水入河方式",
                options=[ft.dropdown.Option(m) for m in entry_methods],
                value=record_data.get('entry_method', '')
            )
            debug_print(page, "27. 入河方式控件创建")

            # 9. 排污口分类
            outlet_type_main_radio = ft.RadioGroup(
                content=ft.Column([
                    ft.Radio(value="工业排污口", label="工业排污口"),
                    ft.Radio(value="城镇污水处理厂排污口", label="城镇污水处理厂排污口"),
                    ft.Radio(value="农业排口", label="农业排口"),
                    ft.Radio(value="其他排口", label="其他排口"),
                    ft.Radio(value="暂无法确定", label="暂无法确定"),
                ]),
                value=record_data.get('outlet_type_main', '')
            )

            sub_options = {
                "工业排污口": ["工业企业排污口", "矿山排污口", "尾矿库排污口", "工业及其他各类园区污水处理厂排污口",
                              "工业企业雨洪排口", "矿山雨洪排口", "尾矿库雨洪排口", "工业及其他各类园区污水处理厂雨洪排口"],
                "农业排口": ["规模化畜禽养殖排污口", "规模化水产养殖排污口"],
                "其他排口": ["大中型灌区排口", "港口码头排口", "规模以下畜禽养殖排污口", "规模以下水产养殖排污口",
                            "城镇生活污水散排口", "农村污水处理设施排污口", "农村生活污水散排口", "城镇雨洪排口", "其他排污"],
            }

            outlet_type_sub_dropdown = ft.Dropdown(
                label="选择二级分类",
                options=[],
                visible=False,
                width=300
            )
            outlet_type_sub_text = ft.TextField(label="具体情况", visible=False, width=300)

            def on_outlet_type_main_change(e):
                main_val = outlet_type_main_radio.value
                if main_val in sub_options:
                    outlet_type_sub_dropdown.options = [ft.dropdown.Option(opt) for opt in sub_options[main_val]]
                    outlet_type_sub_dropdown.value = record_data.get('outlet_type_sub', '') if record_data.get('outlet_type_main') == main_val else ''
                    outlet_type_sub_dropdown.visible = True
                    outlet_type_sub_text.visible = False
                elif main_val == "暂无法确定":
                    outlet_type_sub_dropdown.visible = False
                    outlet_type_sub_text.visible = True
                    outlet_type_sub_text.value = record_data.get('outlet_type_sub', '') if record_data.get('outlet_type_main') == "暂无法确定" else ''
                else:
                    outlet_type_sub_dropdown.visible = False
                    outlet_type_sub_text.visible = False
                page.update()
            outlet_type_main_radio.on_change = on_outlet_type_main_change

            if record_data.get('outlet_type_main'):
                on_outlet_type_main_change(None)
            debug_print(page, "28. 排污口分类控件创建")

            # 10. 责任主体
            responsible_status_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="unknown", label="暂无法确定，需进一步溯源"),
                    ft.Radio(value="known", label="已确定"),
                ]),
                value=record_data.get('responsible_party_status', 'unknown')
            )
            responsible_container.visible = (responsible_status_radio.value == "known")
            add_responsible_btn = ft.ElevatedButton("+ 添加责任主体", on_click=add_responsible, visible=False)

            def on_responsible_status_change(e):
                visible = (responsible_status_radio.value == "known")
                responsible_container.visible = visible
                add_responsible_btn.visible = visible
                page.update()
            responsible_status_radio.on_change = on_responsible_status_change
            on_responsible_status_change(None)
            debug_print(page, "29. 责任主体控件创建")

            # 11. 现场情况
            is_discharging_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="是", label="是"),
                    ft.Radio(value="否", label="否"),
                ]),
                value=record_data.get('is_discharging', '否')
            )
            color_desc = ft.TextField(label="颜色", value=record_data.get('color_desc', ''), visible=True)
            turbidity_desc = ft.TextField(label="浑浊度", value=record_data.get('turbidity_desc', ''), visible=True)
            odor_desc = ft.TextField(label="气味", value=record_data.get('odor_desc', ''), visible=True)

            def on_is_discharging_change(e):
                visible = (is_discharging_radio.value == "是")
                color_desc.visible = visible
                turbidity_desc.visible = visible
                odor_desc.visible = visible
                page.update()
            is_discharging_radio.on_change = on_is_discharging_change
            on_is_discharging_change(None)

            oil_film_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="有", label="有"),
                    ft.Radio(value="无", label="无"),
                ]),
                value=record_data.get('has_oil_film', '无')
            )
            other_issues = ft.TextField(label="其他问题或异常情况", value=record_data.get('other_issues', ''), multiline=True, min_lines=2)
            debug_print(page, "30. 现场情况控件创建")

            # 12. 现场照片（4张）
            photo_images = []
            photo_buttons = []
            photo_status_texts = []

            for i in range(4):
                img = ft.Image(width=200, height=150, fit=ft.ImageFit.CONTAIN, visible=False)
                photo_images.append(img)
                status = ft.Text(f"未拍摄", size=12)
                photo_status_texts.append(status)

                def take_photo(idx=i, target='general'):
                    def on_file_picked(e):
                        if e.files:
                            path = e.files[0].path
                            if target == 'general':
                                photo_paths[idx] = path
                                photo_images[idx].src = path
                                photo_images[idx].visible = True
                                photo_status_texts[idx].value = os.path.basename(path)
                            else:
                                monitor_photo_paths[idx] = path
                                monitor_photo_images[idx].src = path
                                monitor_photo_images[idx].visible = True
                                monitor_photo_status_texts[idx].value = os.path.basename(path)
                            page.update()
                    file_picker = ft.FilePicker(on_result=on_file_picked)
                    page.overlay.append(file_picker)
                    page.update()
                    file_picker.pick_files(allow_multiple=False, allowed_extensions=['jpg', 'jpeg', 'png'])

                btn = ft.ElevatedButton(f"拍摄照片{i+1}", on_click=lambda e, idx=i, t='general': take_photo(idx, t))
                photo_buttons.append(btn)

            if record_id:
                for i in range(4):
                    path = photo_paths[i]
                    if path and os.path.exists(path):
                        photo_images[i].src = path
                        photo_images[i].visible = True
                        photo_status_texts[i].value = os.path.basename(path)
            debug_print(page, "31. 现场照片控件创建")

            # 13. 监测照片
            monitor_photo_images = []
            monitor_photo_buttons = []
            monitor_photo_status_texts = []

            monitor_photo_labels = [
                "监测采样点照片（展示测流及采样条件）",
                "采样或测流工作照片",
                "水样照片（可准确显示水样颜色和浑浊程度）",
                "快检结果照片（各指标合拍）"
            ]

            for i in range(4):
                img = ft.Image(width=200, height=150, fit=ft.ImageFit.CONTAIN, visible=False)
                monitor_photo_images.append(img)
                status = ft.Text(f"未拍摄", size=12)
                monitor_photo_status_texts.append(status)

                btn = ft.ElevatedButton(monitor_photo_labels[i], on_click=lambda e, idx=i, t='monitor': take_photo(idx, t))
                monitor_photo_buttons.append(btn)

            if record_id:
                for i in range(4):
                    path = monitor_photo_paths[i]
                    if path and os.path.exists(path):
                        monitor_photo_images[i].src = path
                        monitor_photo_images[i].visible = True
                        monitor_photo_status_texts[i].value = os.path.basename(path)
            debug_print(page, "32. 监测照片控件创建")

            # 14. 现场监测
            monitor_status_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="yes", label="是"),
                    ft.Radio(value="no", label="否"),
                    ft.Radio(value="unavailable", label="不具备条件"),
                ]),
                value=record_data.get('monitor_status', 'no')
            )
            monitor_unavailable_reason = ft.TextField(label="具体情况", visible=False, multiline=True)
            monitor_container = ft.Column(visible=False)

            monitor_start = ft.TextField(
                label="监测开始时间",
                value=record_data.get('monitor_start_time', ''),
                hint_text="例如 2025-03-11 14:30"
            )
            monitor_end = ft.TextField(
                label="监测结束时间",
                value=record_data.get('monitor_end_time', ''),
                hint_text="例如 2025-03-11 15:30"
            )

            flow_status_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="unavailable", label="不具备测定条件"),
                    ft.Radio(value="unmeasured", label="未测定"),
                    ft.Radio(value="measured", label="现场测定"),
                ]),
                value=record_data.get('flow_status', 'unmeasured')
            )
            flow_value = ft.TextField(label="流量 (m³/s)", value=str(record_data.get('flow_value', '')), visible=False)
            water_temp = ft.TextField(label="水温 (℃)", value=str(record_data.get('water_temp', '')))
            ph_value = ft.TextField(label="pH值", value=str(record_data.get('ph_value', '')))
            conductivity = ft.TextField(label="电导率 (μs/cm)", value=str(record_data.get('conductivity', '')))
            quick_cod = ft.TextField(label="COD (mg/L)", value=str(record_data.get('quick_cod', '')))
            quick_nh3n = ft.TextField(label="氨氮 (mg/L)", value=str(record_data.get('quick_nh3n', '')))
            quick_tp = ft.TextField(label="总磷 (mg/L)", value=str(record_data.get('quick_tp', '')))
            quick_tn = ft.TextField(label="总氮 (mg/L)", value=str(record_data.get('quick_tn', '')))
            other_index = ft.TextField(label="其他指标", value=record_data.get('other_index', ''))

            def on_flow_status_change(e):
                flow_value.visible = (flow_status_radio.value == "measured")
                page.update()
            flow_status_radio.on_change = on_flow_status_change

            monitor_container.controls = [
                ft.Text("监测人员（至少2人）"),
                monitor_people_container,
                ft.ElevatedButton("+ 添加监测人员", on_click=add_monitor_people),
                monitor_start,
                monitor_end,
                ft.Text("流量测定"),
                flow_status_radio,
                flow_value,
                water_temp,
                ph_value,
                conductivity,
                quick_cod,
                quick_nh3n,
                quick_tp,
                quick_tn,
                other_index,
                ft.Divider(),
                ft.Text("监测现场照片"),
                ft.Column([
                    ft.Row([monitor_photo_buttons[0], monitor_photo_status_texts[0]]),
                    monitor_photo_images[0],
                    ft.Row([monitor_photo_buttons[1], monitor_photo_status_texts[1]]),
                    monitor_photo_images[1],
                    ft.Row([monitor_photo_buttons[2], monitor_photo_status_texts[2]]),
                    monitor_photo_images[2],
                    ft.Row([monitor_photo_buttons[3], monitor_photo_status_texts[3]]),
                    monitor_photo_images[3],
                ]),
            ]

            def on_monitor_status_change(e):
                status = monitor_status_radio.value
                monitor_unavailable_reason.visible = (status == "unavailable")
                monitor_container.visible = (status == "yes")
                page.update()
            monitor_status_radio.on_change = on_monitor_status_change
            on_monitor_status_change(None)
            debug_print(page, "33. 现场监测控件创建")

            # 15. 采样送检
            sample_status_radio = ft.RadioGroup(
                content=ft.Row([
                    ft.Radio(value="yes", label="是"),
                    ft.Radio(value="no", label="否"),
                ]),
                value=record_data.get('sample_status', 'no')
            )
            sample_container = ft.Column(visible=False)

            indicators = ["pH值", "化学需氧量", "氨氮", "总磷", "总氮"]
            indicator_checkboxes = []
            for ind in indicators:
                cb = ft.Checkbox(label=ind, value=False)
                indicator_checkboxes.append(cb)

            if record_data.get('sample_indicators'):
                try:
                    selected = json.loads(record_data['sample_indicators'])
                    for cb in indicator_checkboxes:
                        if cb.label in selected:
                            cb.value = True
                except:
                    pass

            other_indicators = ft.TextField(label="其他选测指标", value=record_data.get('other_indicators', ''))
            test_institution = ft.TextField(label="检测机构", value=record_data.get('test_institution', ''))
            sample_arrive_time = ft.TextField(
                label="样品送达时间",
                value=record_data.get('sample_arrive_time', ''),
                hint_text="例如 2025-03-11 16:00"
            )

            sample_container.controls = [
                ft.Text("送检指标（可多选）"),
                ft.Column(indicator_checkboxes),
                other_indicators,
                test_institution,
                sample_arrive_time,
            ]

            def on_sample_status_change(e):
                sample_container.visible = (sample_status_radio.value == "yes")
                page.update()
            sample_status_radio.on_change = on_sample_status_change
            on_sample_status_change(None)
            debug_print(page, "34. 采样送检控件创建")

            # 16. 现场工作人员
            leader = ft.TextField(label="负责人", value=record_data.get('leader', ''))
            leader_phone = ft.TextField(label="联系电话", value=record_data.get('leader_phone', ''))
            add_participant_btn = ft.ElevatedButton("+ 添加参加人员", on_click=add_participant)
            debug_print(page, "35. 现场工作人员控件创建")

            # 17. 备注
            remark = ft.TextField(label="备注", value=record_data.get('remark', ''), multiline=True, min_lines=3)
            debug_print(page, "36. 备注控件创建")

            # ---------- 保存按钮逻辑 ----------
            def save_record(e):
                try:
                    debug_print(page, "37. 开始保存记录")
                    task_val = task_source_radio.value
                    if task_val == "其他":
                        task_val = "其他:" + other_task_field.value

                    # 收集责任主体
                    responsible_parties = []
                    for row in responsible_rows:
                        name = row.controls[0].value
                        industry = row.controls[1].value
                        if name or industry:
                            responsible_parties.append({"name": name, "industry": industry})

                    # 收集参加人员
                    participants_list = [row.value for row in participant_rows if row.value.strip()]

                    # 收集监测人员
                    monitor_people_list = [row.value for row in monitor_people_rows if row.value.strip()]

                    # 收集送检指标
                    selected_indicators = [cb.label for cb in indicator_checkboxes if cb.value]

                    data = {
                        'create_time': datetime.now().isoformat(),
                        'task_source': task_val,
                        'outlet_name': outlet_name.value,
                        'outlet_name_status': name_radio.value,
                        'outlet_code': outlet_code.value,
                        'outlet_code_status': code_radio.value,
                        'province': province.value,
                        'city': city.value,
                        'county': county.value,
                        'town': town.value,
                        'village': village.value,
                        'longitude': float(longitude.value) if longitude.value else 0.0,
                        'latitude': float(latitude.value) if latitude.value else 0.0,
                        'in_national_platform': int(platform_radio.value),
                        'water_body': water_body.value,
                        'water_func_zone1': water_func_zone1.value,
                        'water_func_zone2': water_func_zone2.value,
                        'downstream_section': downstream_section.value,
                        'downstream_distance': float(downstream_distance.value) if downstream_distance.value else 0.0,
                        'entry_method': entry_dropdown.value,
                        'outlet_type_main': outlet_type_main_radio.value,
                        'outlet_type_sub': outlet_type_sub_dropdown.value if outlet_type_sub_dropdown.visible else outlet_type_sub_text.value,
                        'responsible_party_status': responsible_status_radio.value,
                        'responsible_parties': json.dumps(responsible_parties, ensure_ascii=False),
                        'is_discharging': is_discharging_radio.value,
                        'color_desc': color_desc.value,
                        'turbidity_desc': turbidity_desc.value,
                        'odor_desc': odor_desc.value,
                        'has_oil_film': oil_film_radio.value,
                        'other_issues': other_issues.value,
                        'photo1': photo_paths[0],
                        'photo2': photo_paths[1],
                        'photo3': photo_paths[2],
                        'photo4': photo_paths[3],
                        'monitor_status': monitor_status_radio.value,
                        'monitor_unavailable_reason': monitor_unavailable_reason.value if monitor_status_radio.value == "unavailable" else '',
                        'monitor_people': json.dumps(monitor_people_list, ensure_ascii=False),
                        'monitor_start_time': monitor_start.value,
                        'monitor_end_time': monitor_end.value,
                        'flow_status': flow_status_radio.value,
                        'flow_value': float(flow_value.value) if flow_status_radio.value == "measured" and flow_value.value else 0.0,
                        'water_temp': float(water_temp.value) if water_temp.value else 0.0,
                        'ph_value': float(ph_value.value) if ph_value.value else 0.0,
                        'conductivity': float(conductivity.value) if conductivity.value else 0.0,
                        'quick_cod': float(quick_cod.value) if quick_cod.value else 0.0,
                        'quick_nh3n': float(quick_nh3n.value) if quick_nh3n.value else 0.0,
                        'quick_tp': float(quick_tp.value) if quick_tp.value else 0.0,
                        'quick_tn': float(quick_tn.value) if quick_tn.value else 0.0,
                        'other_index': other_index.value,
                        'monitor_photo1': monitor_photo_paths[0],
                        'monitor_photo2': monitor_photo_paths[1],
                        'monitor_photo3': monitor_photo_paths[2],
                        'monitor_photo4': monitor_photo_paths[3],
                        'sample_status': sample_status_radio.value,
                        'sample_indicators': json.dumps(selected_indicators, ensure_ascii=False),
                        'other_indicators': other_indicators.value,
                        'test_institution': test_institution.value,
                        'sample_arrive_time': sample_arrive_time.value,
                        'leader': leader.value,
                        'leader_phone': leader_phone.value,
                        'participants': json.dumps(participants_list, ensure_ascii=False),
                        'remark': remark.value,
                    }

                    if current_edit_id:
                        db.update_record(current_edit_id, data)
                        page.show_snack_bar(ft.SnackBar(content=ft.Text("更新成功！")))
                    else:
                        db.insert_record(data)
                        page.show_snack_bar(ft.SnackBar(content=ft.Text("保存成功！")))
                    show_list_view()
                except Exception as ex:
                    debug_print(page, f"保存失败: {ex}")
                    page.show_snack_bar(ft.SnackBar(content=ft.Text(f"保存失败: {ex}")))

            save_btn = ft.ElevatedButton(
                "保存记录",
                on_click=save_record,
                style=ft.ButtonStyle(color={"": ft.colors.WHITE}, bgcolor={"": ft.colors.BLUE_600}, padding=20),
                width=300
            )
            back_btn = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=lambda e: show_list_view())

            # ---------- 组装表单 ----------
            page.add(
                ft.Row([back_btn, ft.Text("现场记录表单", size=20, weight=ft.FontWeight.BOLD)]),
                ft.Divider(),
                ft.Text("任务来源", size=16, weight=ft.FontWeight.BOLD),
                task_source_radio,
                other_task_field,
                ft.Divider(),
                ft.Text("排污口名称", size=16, weight=ft.FontWeight.BOLD),
                name_radio,
                outlet_name,
                ft.Text("排污口编码", size=16, weight=ft.FontWeight.BOLD),
                code_radio,
                outlet_code,
                ft.Divider(),
                ft.Text("纳入国家平台", size=16, weight=ft.FontWeight.BOLD),
                platform_radio,
                ft.Divider(),
                ft.Text("位置信息", size=16, weight=ft.FontWeight.BOLD),
                province,
                city,
                county,
                town,
                village,
                get_location_btn,
                longitude,
                latitude,
                ft.Divider(),
                ft.Text("水体信息", size=16, weight=ft.FontWeight.BOLD),
                water_body,
                water_func_zone1,
                water_func_zone2,
                downstream_section,
                downstream_distance,
                ft.Divider(),
                ft.Text("入河方式", size=16, weight=ft.FontWeight.BOLD),
                entry_dropdown,
                ft.Divider(),
                ft.Text("排污口分类", size=16, weight=ft.FontWeight.BOLD),
                outlet_type_main_radio,
                outlet_type_sub_dropdown,
                outlet_type_sub_text,
                ft.Divider(),
                ft.Text("责任主体", size=16, weight=ft.FontWeight.BOLD),
                responsible_status_radio,
                responsible_container,
                add_responsible_btn,
                ft.Divider(),
                ft.Text("现场情况", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("正在排放污水:"),
                is_discharging_radio,
                color_desc,
                turbidity_desc,
                odor_desc,
                ft.Text("水面有无油膜:"),
                oil_film_radio,
                other_issues,
                ft.Divider(),
                ft.Text("现场照片", size=16, weight=ft.FontWeight.BOLD),
                ft.Column([
                    ft.Row([photo_buttons[0], photo_status_texts[0]]),
                    photo_images[0],
                    ft.Row([photo_buttons[1], photo_status_texts[1]]),
                    photo_images[1],
                    ft.Row([photo_buttons[2], photo_status_texts[2]]),
                    photo_images[2],
                    ft.Row([photo_buttons[3], photo_status_texts[3]]),
                    photo_images[3],
                ]),
                ft.Divider(),
                ft.Text("现场监测", size=16, weight=ft.FontWeight.BOLD),
                monitor_status_radio,
                monitor_unavailable_reason,
                monitor_container,
                ft.Divider(),
                ft.Text("采样送检", size=16, weight=ft.FontWeight.BOLD),
                sample_status_radio,
                sample_container,
                ft.Divider(),
                ft.Text("现场工作人员", size=16, weight=ft.FontWeight.BOLD),
                leader,
                leader_phone,
                ft.Text("参加人员:"),
                participants_container,
                add_participant_btn,
                ft.Divider(),
                ft.Text("备注", size=16, weight=ft.FontWeight.BOLD),
                remark,
                ft.Divider(),
                ft.Row([save_btn], alignment=ft.MainAxisAlignment.CENTER)
            )
            page.update()
            debug_print(page, "38. 表单页面渲染完成")

        # 启动列表页
        debug_print(page, "39. 准备调用 show_list_view")
        show_list_view()
        debug_print(page, "40. show_list_view 执行完毕")

    except Exception as e:
        # 捕获任何异常并在屏幕上显示
        error_msg = f"启动失败: {str(e)}\n{traceback.format_exc()}"
        debug_print(page, error_msg)
        page.clean()
        page.add(
            ft.Text("启动失败，错误信息：", size=20, color=ft.colors.RED),
            ft.Text(str(e), size=14, selectable=True),
            ft.Text("详细堆栈：", size=16),
            ft.Text(traceback.format_exc(), size=10, selectable=True),
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main)
