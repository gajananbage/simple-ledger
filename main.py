import json
import os
import datetime
from flet import (
    app, Page, Text, TextField, Dropdown, dropdown, ElevatedButton,
    IconButton, Row, Column, Container, DataTable, DataColumn,
    DataRow, DataCell, Colors, FilePicker,
    AlertDialog, TextButton, icons, ScrollMode, MainAxisAlignment,
    CrossAxisAlignment, SnackBar
)

def main(page: Page):
    page.title = "Simple Ledger"
    page.max_width = 900
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.scroll = ScrollMode.AUTO
    page.theme_mode = "light"

    # State
    current_person = [None]  # list for mutability
    ledger_data = {}

    DATA_FILE = "ledger_store.json"

    # Load data
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    ledger_data = json.loads(content)
    except Exception as e:
        print("Load error:", e)
        ledger_data = {}

    def save_to_storage():
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(ledger_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            page.open(AlertDialog(title=Text(f"Save Error: {str(e)}")))
            return False

    def show_snack(message: str, color=Colors.GREEN):
        page.show_snack_bar(SnackBar(Text(message), bgcolor=color))

    def show_error(message: str):
        page.open(AlertDialog(title=Text(message, color=Colors.RED)))

    def get_balance(name):
        entries = ledger_data.get(name, [])
        return sum(e['a'] if e['t'] else -e['a'] for e in entries)

    def fmt_money(n):
        return f"₹{round(n):,}"

    # ====================== File Operations ======================
    def on_export(e):
        if e.path:
            try:
                with open(e.path, "w", encoding="utf-8") as f:
                    json.dump(ledger_data, f, indent=2, ensure_ascii=False)
                show_snack("Backup saved successfully!")
            except Exception as ex:
                show_error(f"Export error: {ex}")

    def on_import(e):
        if e.files:
            try:
                with open(e.files[0].path, "r", encoding="utf-8") as f:
                    imported = json.load(f)
                ledger_data.clear()
                ledger_data.update(imported)
                save_to_storage()
                update_people_list()
                show_snack("Data restored successfully!")
            except Exception as ex:
                show_error(f"Import error: {ex}")

    file_picker_export = FilePicker(on_result=on_export)
    file_picker_import = FilePicker(on_result=on_import)
    page.overlay.extend([file_picker_export, file_picker_import])

    # ====================== Event Handlers ======================
    def on_search_change(e):
        update_people_list()

    def add_new_person(e):
        def close_dialog(evt):
            page.close(dialog)

        def confirm_add(evt):
            name = name_input.value.strip()
            if not name:
                show_error("नाव रिकामे असू शकत नाही!")
                return
            if name in ledger_data:
                show_error("हे नाव आधीपासून आहे!")
                return
            ledger_data[name] = []
            save_to_storage()
            page.close(dialog)
            open_person(name)
            show_snack(f"{name} जोडला गेला")

        name_input = TextField(label="नाव टाका", autofocus=True)
        dialog = AlertDialog(
            title=Text("नवीन व्यक्ती जोडा"),
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
            if name in ledger_data:
                del ledger_data[name]
                save_to_storage()
            if current_person[0] == name:
                current_person[0] = None
                main_view.visible = False
            page.close(dialog)
            update_people_list()
            show_snack(f"{name} डिलीट केला")

        dialog = AlertDialog(
            title=Text("खात्री आहे?"),
            content=Text(f"तुम्हाला {name} चा सर्व डेटा डिलीट करायचा आहे का?"),
            actions=[
                TextButton("नाही", on_click=close_dialog),
                TextButton("हो, डिलीट करा", on_click=confirm_delete, style="color: red")
            ]
        )
        page.open(dialog)

    def open_person(name):
        current_person[0] = name
        main_view.visible = True
        person_title.value = name
        render_person_ledger()
        page.update()

    def save_entry(e):
        if not amt_input.value:
            show_error("रक्कम टाका!")
            return
        try:
            amt = float(amt_input.value)
            if amt <= 0:
                raise ValueError
        except ValueError:
            show_error("वैध रक्कम टाका!")
            return

        is_credit = type_dropdown.value == "1"
        now_dt = datetime.datetime.now()
        date_str = now_dt.strftime("%d/%m/%Y %H:%M")
        note = desc_input.value.strip() or ("+ प्राप्त" if is_credit else "- दिले")

        if current_person[0] not in ledger_data:
            ledger_data[current_person[0]] = []

        ledger_data[current_person[0]].append({
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
        show_snack("Entry जोडली गेली")

    def delete_entry(index):
        if current_person[0] and current_person[0] in ledger_data:
            ledger_data[current_person[0]].pop(index)
            save_to_storage()
            render_person_ledger()
            update_people_list()
            show_snack("Entry डिलीट केली")

    # ====================== UI Components ======================
    search_input = TextField(
        label="नाव शोधा...",
        width=300,
        on_change=on_search_change
    )

    top_bar = Row(
        controls=[
            search_input,
            ElevatedButton("+ नवीन", on_click=add_new_person, icon=icons.ADD),
            ElevatedButton("बॅकअप", on_click=lambda _: file_picker_export.save_file(file_name="ledger_backup.json")),
            ElevatedButton("रिस्टोर", on_click=lambda _: file_picker_import.pick_files(allowed_extensions=["json"])),
        ],
        alignment=MainAxisAlignment.CENTER,
        wrap=True
    )

    people_container = Column(horizontal_alignment=CrossAxisAlignment.CENTER, spacing=8)
    person_title = Text("", size=24, weight="bold")

    desc_input = TextField(label="नोंद (ऐच्छिक)", width=250)
    amt_input = TextField(label="रक्कम", keyboard_type="number", width=150)
    type_dropdown = Dropdown(
        value="1",
        width=100,
        options=[
            dropdown.Option("1", "प्राप्त (+)"),
            dropdown.Option("0", "दिले (–)")
        ]
    )

    balance_summary = Text("₹0", size=26, weight="bold", color=Colors.GREEN)

    ledger_table = DataTable(
        columns=[
            DataColumn(Text("दिनांक")),
            DataColumn(Text("नोंद")),
            DataColumn(Text("प्राप्त"), numeric=True),
            DataColumn(Text("दिले"), numeric=True),
            DataColumn(Text("बॅलन्स"), numeric=True),
            DataColumn(Text(""))
        ],
        rows=[],
        width=850
    )

    main_view = Column(
        visible=False,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=15,
        controls=[
            Row(
                [person_title, IconButton(icon=icons.DELETE, icon_color=Colors.RED, on_click=lambda _: delete_person(current_person[0]))],
                alignment=MainAxisAlignment.CENTER
            ),
            Row(
                [desc_input, amt_input, type_dropdown, ElevatedButton("जोडा", icon=icons.ADD, on_click=save_entry)],
                alignment=MainAxisAlignment.CENTER,
                wrap=True
            ),
            Row([Text("एकूण शिल्लक:", size=18), balance_summary], alignment=MainAxisAlignment.CENTER),
            Container(content=ledger_table, width=880, padding=10)
        ]
    )

    def update_people_list():
        query = search_input.value.lower().strip()
        people_container.controls.clear()
        keys = list(ledger_data.keys())
        if query:
            keys = [k for k in keys if query in k.lower()]
        keys.sort()

        if not keys:
            people_container.controls.append(Text("कोणतेही रेकॉर्ड नाहीत", italic=True, size=16))
        else:
            for k in keys:
                b = get_balance(k)
                bal_color = Colors.GREEN if b >= 0 else Colors.RED
                people_container.controls.append(
                    Row([
                        ElevatedButton(
                            content=Row([
                                Text(k, size=16),
                                Text(fmt_money(b), color=bal_color, weight="bold")
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            width=320,
                            on_click=lambda _, name=k: open_person(name)
                        ),
                        IconButton(
                            icon=icons.DELETE,
                            icon_color=Colors.RED,
                            on_click=lambda _, name=k: delete_person(name)
                        )
                    ], alignment=MainAxisAlignment.CENTER)
                )
        page.update()

    def render_person_ledger():
        entries = ledger_data.get(current_person[0], [])
        # Sort by date (newest first)
        entries.sort(
            key=lambda x: datetime.datetime.strptime(x['d'], "%d/%m/%Y %H:%M"),
            reverse=True
        )

        ledger_table.rows.clear()
        running_bal = 0

        for i, e in enumerate(entries):
            running_bal += e['a'] if e['t'] else -e['a']
            bal_color = Colors.GREEN if running_bal >= 0 else Colors.RED

            ledger_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(e['d'], size=13)),
                    DataCell(Text(e['c'], size=13)),
                    DataCell(Text(str(round(e['a'])) if e['t'] else "", color=Colors.GREEN if e['t'] else None)),
                    DataCell(Text(str(round(e['a'])) if not e['t'] else "", color=Colors.RED if not e['t'] else None)),
                    DataCell(Text(fmt_money(running_bal), color=bal_color, weight="bold")),
                    DataCell(IconButton(
                        icon=icons.CLOSE,
                        icon_color=Colors.RED_400,
                        on_click=lambda _, idx=i: delete_entry(idx)
                    ))
                ])
            )

        balance_summary.value = fmt_money(running_bal)
        balance_summary.color = Colors.GREEN if running_bal >= 0 else Colors.RED
        page.update()

    # ====================== Main UI ======================
    page.add(
        Column(
            controls=[
                Text("सिंपल लेजर", size=32, weight="bold"),
                top_bar,
                Container(height=2, bgcolor=Colors.GREY_400, width=800),
                people_container,
                Container(height=2, bgcolor=Colors.GREY_400, width=800),
                main_view
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

    update_people_list()


app(target=main)