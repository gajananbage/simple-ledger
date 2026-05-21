import json
import datetime
from flet import (
    app, Page, Text, TextField, Dropdown, dropdown, ElevatedButton, 
    IconButton, Row, Column, Container, DataTable, DataColumn, 
    DataRow, DataCell, colors, FilePicker, FilePickerResultEvent,
    AlertDialog, TextButton, icons, ScrollMode, MainAxisAlignment, CrossAxisAlignment
)

def main(page: Page):
    page.title = "Simple Ledger"
    page.max_width = 800
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.scroll = ScrollMode.AUTO

    # State variables
    current_person = None
    
    # Fetch initial ledger data from client storage (localStorage equivalent)
    if page.client_storage.contains_key("ledger"):
        try:
            ledger_data = json.loads(page.client_storage.get("ledger"))
        except:
            ledger_data = {}
    else:
        ledger_data = {}

    def save_to_storage():
        page.client_storage.set("ledger", json.dumps(ledger_data))

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
            page.dialog.open = False
            page.update()

        def confirm_add(evt):
            name = name_input.value.strip()
            if not name:
                return
            if name in ledger_data:
                page.snack_bar = AlertDialog(title=Text("Name already exists!"))
                page.snack_bar.open = True
                page.update()
                return
            ledger_data[name] = []
            save_to_storage()
            page.dialog.open = False
            open_person(name)

        name_input = TextField(label="Name", autofocus=True)
        page.dialog = AlertDialog(
            title=Text("Enter Name"),
            content=name_input,
            actions=[
                TextButton("Cancel", on_click=close_dialog),
                TextButton("Add", on_click=confirm_add)
            ]
        )
        page.dialog.open = True
        page.update()

    def delete_person(name):
        def close_dialog(evt):
            page.dialog.open = False
            page.update()

        def confirm_delete(evt):
            nonlocal current_person
            if name in ledger_data:
                del ledger_data[name]
                save_to_storage()
            if current_person == name:
                current_person = None
                main_view.visible = False
            page.dialog.open = False
            update_people_list()

        page.dialog = AlertDialog(
            title=Text("Confirm Delete"),
            content=Text(f"Delete entire record for {name}?"),
            actions=[
                TextButton("Cancel", on_click=close_dialog),
                TextButton("Delete", on_click=confirm_delete)
            ]
        )
        page.dialog.open = True
        page.update()

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

    # --- Backup & Restore Handlers ---
    
    def export_data(e):
        if not ledger_data:
            return
        # In Flet apps, creating an accessible local download for Mobile requires 
        # file picker paths. For standard cross-platform implementation, we output a save picker.
        file_picker_export.save_file(
            file_name=f"ledger_backup_{datetime.date.today().isoformat()}.json",
            allowed_extensions=["json"]
        )

    def on_export_result(e: FilePickerResultEvent):
        if e.path:
            with open(e.path, "w") as f:
                json.dump(ledger_data, f, indent=2)

    def import_data(e):
        file_picker_import.pick_files(allowed_extensions=["json"])

    def on_import_result(e: FilePickerResultEvent):
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
            except Exception:
                pass

    file_picker_export = FilePicker(on_result=on_export_result)
    file_picker_import = FilePicker(on_result=on_import_result)
    page.overlay.extend([file_picker_export, file_picker_import])

    # --- UI Rendering Functions ---

    def update_people_list():
        query = search_input.value.lower().strip()
        people_container.controls.clear()

        keys = list(ledger_data.keys())
        if query:
            keys = [k for k in keys if query in k.lower()]
            # Simple sorting matching the original logic
            keys.sort(key=lambda k: (0 if k.lower() == query else 1, -get_balance(k)))
        else:
            keys.sort(key=lambda k: -get_balance(k))

        if not keys:
            people_container.controls.append(Text("No matches or no records yet", italic=True))
        else:
            for k in keys:
                b = get_balance(k)
                bal_color = colors.GREEN if b >= 0 else colors.RED
                
                # Closures to hold correct 'k' reference
                def make_click(name): return lambda _: open_person(name)
                def make_delete(name): return lambda _: delete_person(name)

                row_item = Row(
                    controls=[
                        ElevatedButton(
                            content=Row([
                                Text(k), 
                                Text(fmt_money(b), color=bal_color, weight="bold")
                            ], alignment=MainAxisAlignment.SPACE_BETWEEN),
                            width=220,
                            on_click=make_click(k)
                        ),
                        IconButton(
                            icon=icons.DELETE_FOREGROUND, 
                            icon_color=colors.RED, 
                            on_click=make_delete(k)
                        )
                    ],
                    alignment=MainAxisAlignment.CENTER
                )
                people_container.controls.append(row_item)
        page.update()

    def render_person_ledger():
        entries = ledger_data.get(current_person, [])
        ledger_table.rows.clear()
        
        running_bal = 0
        for i, e in enumerate(entries):
            running_bal += e['a'] if e['t'] else -e['a']
            bal_color = colors.GREEN if running_bal >= 0 else colors.RED
            
            def make_del_entry(idx): return lambda _: delete_entry(idx)

            ledger_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(e['d'])),
                    DataCell(Text(e['c'])),
                    DataCell(Text(str(round(e['a'])) if e['t'] else "")),
                    DataCell(Text(str(round(e['a'])) if not e['t'] else "")),
                    DataCell(Text(fmt_money(running_bal), color=bal_color, weight="bold")),
                    DataCell(IconButton(icon=icons.CLOSE, icon_color=colors.RED_400, on_click=make_del_entry(i)))
                ])
            )
        
        balance_summary.value = fmt_money(running_bal)
        balance_summary.color = colors.GREEN if running_bal >= 0 else colors.RED
        page.update()

    # --- UI Architecture Layout Layout ---
    
    # Top elements
    search_input = TextField(label="Search name...", size=30, autofocus=True, on_change=on_search_change)
    top_bar = Row(
        controls=[
            search_input,
            ElevatedButton("+ New", on_click=add_new_person),
            ElevatedButton("Backup", on_click=export_data),
            ElevatedButton("Restore", on_click=import_data)
        ],
        alignment=MainAxisAlignment.CENTER,
        wrap=True
    )

    people_container = Column(horizontal_alignment=CrossAxisAlignment.CENTER)

    # Detailed view for selected person (initially hidden)
    person_title = Text("", size=22, weight="bold")
    desc_input = TextField(label="Note (optional)", width=200)
    amt_input = TextField(label="Amt", width=100, keyboard_type="number")
    type_dropdown = Dropdown(
        value="1",
        width=80,
        options=[
            dropdown.Option("1", "+"),
            dropdown.Option("0", "–"),
        ]
    )
    balance_summary = Text("₹0", size=24, weight="bold")
    
    ledger_table = DataTable(
        columns=[
            DataColumn(Text("Date")),
            DataColumn(Text("Note")),
            DataColumn(Text("+")),
            DataColumn(Text("–")),
            DataColumn(Text("Bal")),
            DataColumn(Text("Del")),
        ],
        rows=[]
    )

    main_view = Column(
        visible=False,
        horizontal_alignment=CrossAxisAlignment.CENTER,
        controls=[
            Row([
                person_title, 
                IconButton(icon=icons.DELETE, icon_color=colors.RED, on_click=lambda _: delete_person(current_person))
            ], alignment=MainAxisAlignment.CENTER),
            Row([desc_input, amt_input, type_dropdown, ElevatedButton("Add", on_click=save_entry)], alignment=MainAxisAlignment.CENTER, wrap=True),
            Row([Text("Balance: ", size=18), balance_summary], alignment=MainAxisAlignment.CENTER),
            Container(content=ledger_table, overflow_x=ScrollMode.AUTO)
        ]
    )

    # Bootstrapping View
    page.add(
        Column(
            controls=[
                Text("Simple Ledger", size=28, weight="bold"),
                top_bar,
                Container(height=1, bgcolor=colors.GREY_300),
                people_container,
                Container(height=1, bgcolor=colors.GREY_300),
                main_view
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER,
            spacing=20
        )
    )
    
    # Initialize people list
    update_people_list()

app(target=main)
