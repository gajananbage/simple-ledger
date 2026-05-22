import json
import time
import datetime
from flet import (
    app, Page, Text, TextField, Dropdown, dropdown, ElevatedButton, 
    IconButton, Row, Column, Container, DataTable, DataColumn, 
    DataRow, DataCell, Colors, FilePicker,
    AlertDialog, TextButton, icons, ScrollMode, MainAxisAlignment, CrossAxisAlignment
)

def main(page: Page):
    page.title = "Simple Ledger"
    page.max_width = 800
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.scroll = ScrollMode.AUTO

    # स्टेट व्हेरिएबल्स
    current_person = None
    ledger_data = {}

    # मुख्य लेआउट (UI कंट्रोलर)
    main_layout = Column(horizontal_alignment=CrossAxisAlignment.CENTER, spacing=20)
    page.add(main_layout)

    def save_to_storage():
        try:
            # नवीन Flet व्हर्जननुसार डेटा सेव्ह करण्याची योग्य पद्धत
            page.client_storage.set("ledger_data_key", json.dumps(ledger_data))
        except Exception as e:
            page.open(AlertDialog(title=Text(f"Save Error: {str(e)}")))

    def get_balance(name):
        entries = ledger_data.get(name, [])
        return sum(e['a'] if e['t'] else -e['a'] for e in entries)

    def fmt_money(n):
        return f"₹{round(n)}"

    # --- UI Event Handlers ---
    def on_search_change(e):
        update_people_list()

    def add_new_person(e):
        def close_dialog(evt):
            page.close(dialog)

        def confirm_add(evt):
            name = name_input.value.strip()
            if not name:
                return
            if name in ledger_data:
                page.open(AlertDialog(title=Text("नाव आधीपासूनच आहे!")))
                return
            ledger_data[name] = []
            save_to_storage()
            page.close(dialog)
            open_person(name)

        name_input = TextField(label="नाव टाका", autofocus=True)
        dialog = AlertDialog(
            title=Text("नवीन नाव जोडा"),
            content=name_input,
            actions=[
                TextButton("रद्द करा", on_click=close_dialog),
                TextButton("जोडा", on_click=confirm_add)
            ]
        )
        page.open(dialog)

    def delete_person(name):
        def close_dialog(evt):
            page.close(dialog)

        def confirm_delete(evt):
            nonlocal current_person
            if name in ledger_data:
                del ledger_data[name]
                save_to_storage()
            if current_person == name:
                current_person = None
                main_view.visible = False
            page.close(dialog)
            update_people_list()

        dialog = AlertDialog(
            title=Text("डिलीट करायचे?"),
            content=Text(f"तुम्हाला नक्की {name} चा रेकॉर्ड डिलीट करायचा आहे का?"),
            actions=[
                TextButton("नाही", on_click=close_dialog),
                TextButton("हो, डिलीट करा", on_click=confirm_delete)
            ]
        )
        page.open(dialog)

    def open_person(name):
        nonlocal current_person
        current_person = name
        main_view.visible = True
        person_title.value = name
        render_person_ledger()

    def save_entry(e):
        if not amt_input.value:
            return
        try:
            amt = float(amt_input.value)
            if amt <= 0: raise ValueError
        except ValueError:
            return

        is_credit = type_dropdown.value == "1"
        now_dt = datetime.datetime.now()
        date_str = now_dt.strftime("%d/%m/%Y %H:%M")
        
        note = desc_input.value.strip() or ("+" if is_credit else "–")

        if current_person not in ledger_data:
            ledger_data[current_person] = []

        ledger_data[current_person].append({
            "d": date_str,
            "c": note,
            "a": amt,
            "t": is_credit
        })

        save_to_storage()
        desc_input.value = ""
        amt_input.value = ""
        render_person_ledger()
        update_people_list()

    def delete_entry(index):
        if current_person and current_person in ledger_data:
            ledger_data[current_person].pop(index)
            save_to_storage()
            render_person_ledger()
            update_people_list()

    # --- Backup & Restore ---
    def export_data(e):
        if not ledger_data:
            return
        file_picker_export.save_file(
            file_name=f"ledger_backup_{datetime.date.today().isoformat()}.json",
            allowed_extensions=["json"]
        )

    def on_export_result(e):
        if e.path:
            with open(e.path, "w") as f:
                json.dump(ledger_data, f, indent=2)

    def import_data(e):
        file_picker_import.pick_files(allowed_extensions=["json"])

    def on_import_result(e):
        nonlocal ledger_data, current_person
        if e.files:
            file_path = e.files[0].path
            try:
                with open(file_path, "r") as f:
                    imported = json.load(f)
                ledger_data = imported
                save_to_storage()
                current_person = None
                main_view.visible = False
                update_people_list()
            except:
                pass

    file_picker_export = FilePicker(on_result=on_export_result)
    file_picker_import = FilePicker(on_result=on_import_result)
    page.overlay.extend([file_picker_export, file_picker_import])

    # --- UI Components ---
    search_input = TextField(label="नाव शोधा...", size=30, on_change=on_search_change)
    top_bar = Row(
        controls=[
            search_input,
            ElevatedButton("+ नवीन", on_click=add_new_person),
            ElevatedButton("बॅकअप", on_click=export_data),
            ElevatedButton("रिस्टोर", on_click=import_data)
        ],
        alignment=MainAxisAlignment.CENTER,
        wrap=True
    )

    people_container = Column(horizontal_alignment=CrossAxisAlignment.CENTER)
    person_title = Text("", size=22, weight="bold")
    desc_input = TextField(label="नोंद (ऐच्छिक)", width=200)
    amt_input = TextField(label="रक्कम", width=100, keyboard_type="number")
    type_dropdown = Dropdown(
        value="1",
        width=80,
        options=[dropdown.Option("1", "+"), dropdown.Option("0", "–")]
    )
    balance_summary = Text("₹0", size=24, weight="bold")
    
    ledger_table = DataTable(
        columns=[
            DataColumn(Text("दिनांक")), DataColumn(Text("नोंद")),
            DataColumn(Text("+")), DataColumn(Text("–")),
            DataColumn(Text("बॅलन्स")), DataColumn(Text("कट"))
        ],
        rows=[]
    )

    main_view = Column(
        visible=False,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        controls=[
            Row([person_title, IconButton(icon=icons.DELETE, icon_color=Colors.RED, on_click=lambda _: delete_person(current_person))], alignment=MainAxisAlignment.CENTER),
            Row([desc_input, amt_input, type_dropdown, ElevatedButton("ऐड करा", on_click=save_entry)], alignment=MainAxisAlignment.CENTER, wrap=True),
            Row([Text("एकूण शिल्लक: ", size=18), balance_summary], alignment=MainAxisAlignment.CENTER),
            Container(content=ledger_table, overflow_x=ScrollMode.AUTO)
        ]
    )

    def update_people_list():
        query = search_input.value.lower().strip()
        people_container.controls.clear()
        keys = list(ledger_data.keys())
        if query:
            keys = [k for k in keys if query in k.lower()]
            keys.sort(key=lambda k: (0 if k.lower() == query else 1, -get_balance(k)))
        else:
            keys.sort(key=lambda k: -get_balance(k))

        if not keys:
            people_container.controls.append(Text("कोणतेही रेkकॉर्ड नाही", italic=True))
        else:
            for k in keys:
                b = get_balance(k)
                bal_color = Colors.GREEN if b >= 0 else Colors.RED
                def make_click(name): return lambda _: open_person(name)
                def make_delete(name): return lambda _: delete_person(name)
                people_container.controls.append(
                    Row([
                        ElevatedButton(content=Row([Text(k), Text(fmt_money(b), color=bal_color, weight="bold")], alignment=MainAxisAlignment.SPACE_BETWEEN), width=220, on_click=make_click(k)),
                        IconButton(icon=icons.DELETE_FOREGROUND, icon_color=Colors.RED, on_click=make_delete(k))
                    ], alignment=MainAxisAlignment.CENTER)
                )
        page.update()

    def render_person_ledger():
        entries = ledger_data.get(current_person, [])
        ledger_table.rows.clear()
        running_bal = 0
        for i, e in enumerate(entries):
            running_bal += e['a'] if e['t'] else -e['a']
            bal_color = Colors.GREEN if running_bal >= 0 else Colors.RED
            def make_del_entry(idx): return lambda _: delete_entry(idx)
            ledger_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(e['d'])), DataCell(Text(e['c'])),
                    DataCell(Text(str(round(e['a'])) if e['t'] else "")),
                    DataCell(Text(str(round(e['a'])) if not e['t'] else "")),
                    DataCell(Text(fmt_money(running_bal), color=bal_color, weight="bold")),
                    DataCell(IconButton(icon=icons.CLOSE, icon_color=Colors.RED_400, on_click=make_del_entry(i)))
                ])
            )
        balance_summary.value = fmt_money(running_bal)
        balance_summary.color = Colors.GREEN if running_bal >= 0 else Colors.RED
        page.update()

    # --- ॲप सुरू होताना ब्लँक स्क्रीन टाळण्यासाठी सुरक्षित लोड सिस्टीम ---
    def initialize_app():
        nonlocal ledger_data
        try:
            # अँड्रॉइडला स्टोरेज लोड करण्यासाठी १ सेकंदाचा वेळ देणे जेणेकरून ते क्रॅश होणार नाही
            time.sleep(1.0) 
            if page.client_storage.contains_key("ledger_data_key"):
                raw = page.client_storage.get("ledger_data_key")
                if raw:
                    ledger_data = json.loads(raw)
        except:
            ledger_data = {}
        
        # आता UI स्क्रीनवर दाखवणे
        main_layout.controls.extend([
            Text("सिंपल लेजर", size=28, weight="bold"),
            top_bar,
            Container(height=1, bgcolor=Colors.GREY_300),
            people_container,
            Container(height=1, bgcolor=Colors.GREY_300),
            main_view
        ])
        update_people_list()

    # इनिशियलायझेशन रन करणे
    initialize_app()

app(target=main)
