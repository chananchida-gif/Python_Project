from pathlib import Path
from tkinter import *
from tkinter import ttk
import tkinter.messagebox
from datetime import datetime
from tkcalendar import Calendar
import sqlite3
from PIL import Image, ImageTk
import os
import shutil
from tkinter import filedialog
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage 
import customtkinter
import re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from tkinter.filedialog import asksaveasfilename
import subprocess
import platform
from collections import defaultdict

# สร้างฐานข้อมูล
conn = sqlite3.connect(r"C:\Users\chanan\Desktop\Drug stock\ya.db")
c = conn.cursor()

# c.execute('''CREATE TABLE product(
#               product_id TEXT PRIMARY KEY, 
#               name TEXT NOT NULL,
#               category TEXT NOT NULL,
#               stock INTEGER NOT NULL,
#               price INTEGER NOT NULL,  
#               manufacture_date TEXT NOT NULL,
#               expiry_date TEXT NOT NULL,
#               supplier TEXT NOT NULL,
#               image_path TEXT NOT NULL)''')

logins = sqlite3.connect(r"C:\Users\chanan\Desktop\Drug stock\login.db")
s = logins.cursor()
# s.execute('''CREATE TABLE users(
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             username TEXT NOT NULL UNIQUE, 
#             password TEXT NOT NULL,
#             email TEXT NOT NULL UNIQUE,
#             birthday TEXT NOT NULL,
#             cardnumber TEXT NOT NULL UNIQUE,
#             address TEXT NOT NULL,
#             phone TEXT NOT NULL UNIQUE,
#             image_path TEXT NOT NULL,
#             role TEXT NOT NULL)''')

# หน้าจอหลัก 
def main_window(root):
    root.deiconify()

    OUTPUT_PATH = Path(__file__).parent #เก็บเส้นทางเป็นทางไปโฟนเดอ
    ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\chanan\Desktop\build\assets\frame0") # เชื่อมตำแหน่งไฟล์ที่เก็บ GUI และปุ่มย่อย
    def relative_to_assets(path: str) -> Path: #รับพารามิเตอร์มา
        return ASSETS_PATH / Path(path) #ส่งค่ากลับมาทำให้หาตำแหน่งเจอ
        
    canvas = Canvas( root,bg = "#EBF8FE",height = 800, width = 1259,bd = 0,highlightthickness = 0,relief = "ridge")
    canvas.place(x = 0, y = 0)
    canvas.create_rectangle(0.0,0.0,1290.0,159.0,fill="#5C7FCB",outline="")
    canvas.create_text(375.0,14.0,anchor="nw",text="คลังสินค้าร้ายขายยา ",fill="#FFFFFF",font=("Inter SemiBold", 60 * -1))

    style = ttk.Style()
    style.theme_use("clam") # เปลี่ยนธีมให้ดูเรียบง่ายและเข้ากับ ttk
    style.configure("Custom.Treeview",rowheight=35,  # ปรับความสูงของแถว
        font=("Arial", 12),  # ตั้งค่าขนาดและฟอนต์ของตัวหนังสือในแถว
        bordercolor="#5C7FCB",borderwidth=1,  # ความหนาของเส้นขอบ
        highlightthickness=1, highlightcolor="#5C7FCB", relief="solid"  # การแสดงผลขอบ
    )
    style.configure("Custom.Treeview.Heading", font=("Arial", 12, "bold"),background="#5C7FCB", foreground="#FFFFFF") # ตั้งค่าหัวตาราง

    def determine_status(stock, expiry_date_str):
        status_list = []

        # ตรวจสอบสถานะสต็อก
        try:
            stock = int(stock)  # แปลงค่า stock เป็นตัวเลข
            if stock <= 0:
                status_list.append("สินค้าหมดสต็อก")
            elif stock <= 5:
                status_list.append("ใกล้หมดสต็อก")
        except (ValueError, TypeError):
            status_list.append("จำนวนสต็อกไม่ถูกต้อง")

        # ตรวจสอบสถานะวันหมดอายุ
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%d/%m/%Y")
            days_to_expiry = (expiry_date - datetime.now()).days
            if days_to_expiry < 0:
                status_list.append("สินค้าหมดอายุ")
            elif days_to_expiry <= 30:
                status_list.append("สินค้าใกล้หมดอายุ") 
        except ValueError:
            # ถ้าวันหมดอายุไม่ถูกต้อง ให้ระบุว่าวันหมดอายุไม่ถูกต้อง
            status_list.append("วันหมดอายุไม่ถูกต้อง")

        # ถ้าสถานะว่างเปล่าแสดงว่าสินค้าพร้อมใช้งาน
        if not status_list:
            status_list.append("สินค้าพร้อมใช้งาน")

        return " และ\n".join(status_list)

    def open_show():
        global show_root
        global tree
        
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if show_root is not None and show_root.winfo_exists():
            show_root.destroy()
            
        show_root = Toplevel(root)
        show_root.title("แสดงรายการสินค้า")
        show_root.geometry("1239x506+10+206")
        show_root.configure(background="#8FB1E0")

        # สร้าง canvas สำหรับแถบด้านบน
        show_canvas = Canvas(show_root, bg="#5C7FCB", height=60, highlightthickness=0, relief="ridge")
        show_canvas.grid(row=0, column=0, columnspan=2, sticky="ew")
        show_canvas.create_text(10, 20, anchor="nw", text="แสดงรายการสินค้า", fill="#FFFFFF", font=("Inter SemiBold", 20))

        # ป้ายข้อความและ entry + ปุ่มใน Frame เดียวกัน
        frame_input = Frame(show_root, bg="#8FB1E0")
        frame_input.grid(row=1, column=0, columnspan=2)

        # ป้ายข้อความ
        Label(frame_input, text="รหัสสินค้าหรือชื่อสินค้าที่ต้องการค้นหา:", 
        font=("Inter SemiBold", 17), bg="#8FB1E0").grid(row=0, column=0, padx=10)

        # ช่องพิมพ์
        entry_id = Entry(frame_input, foreground="#5C7FCB",font=("Inter SemiBold", 16), bg="#EBF8FE")
        entry_id.grid(row=0, column=1, padx=5)

        # สร้าง Frame สำหรับ Treeview
        tree_frame = Frame(show_root, bg="#8FB1E0")
        tree_frame.grid(row=3, column=0,columnspan=3, pady=10, sticky="nsew")

        show_root.rowconfigure(3, weight=1)
        show_root.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=2)
        tree_frame.columnconfigure(0, weight=1)
                                   

        # สร้าง Treeview
        tree = ttk.Treeview(tree_frame, columns=("product_id", "name", "category", "stock", "price", "manufacture_date", "expiry_date", "supplier", "status"), 
                            show="headings", height=20, style="Custom.Treeview")

        tree.heading("product_id", text="รหัสสินค้า")
        tree.heading("name", text="ชื่อยา") 
        tree.heading("category", text="รูปแบบ")
        tree.heading("stock", text="จำนวน")
        tree.heading("price", text="ราคา")
        tree.heading("manufacture_date", text="วันที่ผลิต")
        tree.heading("expiry_date", text="วันหมดอายุ")
        tree.heading("supplier", text="บริษัทนำเข้ายา")
        tree.heading("status", text="สถานะ")

        tree.column("product_id", width=60)
        tree.column("name", width=200)
        tree.column("category", width=100)
        tree.column("stock", width=80)
        tree.column("price", width=80)
        tree.column("manufacture_date", width=80)
        tree.column("expiry_date", width=80)
        tree.column("supplier", width=120)
        tree.column("status", width=120)
        # ปรับตำแหน่ง Treeview และ Scrollbar 
        tree.grid(row=0, column=0, sticky="nsew")

        # เพิ่ม Scrollbar แนวตั้ง
        tree_scroll_y = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=tree_scroll_y.set)

        def pop_up(image_path):
            root_pic = Toplevel()
            root_pic.title("แสดงรูปภาพสินค้า")
            root_pic.geometry("300x300+100+100")
            root_pic.configure(bg="#EBF8FE")
            root_pic.grab_set()  # ล็อกการใช้งานหน้าต่างอื่นจนกว่าจะปิด

            try:
                # โหลดและแสดงรูปภาพ
                img = Image.open(image_path)
                img = img.resize((250, 250), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(img)

                show_pic = Label(root_pic, image=img, bg="#EBF8FE")
                show_pic.image = img 
                show_pic.pack(pady=20)
            except Exception as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงรูปภาพได้: {e}")

        def on_item_select(event):
            item = tree.selection()
            if item:
                product_id = tree.item(item, "values")[0]
                
                try:
                    c.execute("SELECT image_path FROM product WHERE product_id = ?", (product_id,))
                    result = c.fetchone()
                    if result:
                        image_path = result[0]
                        pop_up(image_path)
                    else:
                        tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบรูปภาพสำหรับสินค้านี้")
                except sqlite3.Error as e:
                    tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการดึงข้อมูล: {e}")
        
        tree.bind("<ButtonRelease-1>", on_item_select)
        
        def show_product():
            tree.delete(*tree.get_children())#ล้างค่าทั้งหมดใน Treeview 
            search_term = entry_id.get().strip() 

            try:
                if search_term: #ค้นหาค่าที่พิมพ์ค้นหาในช่องกรอก
                    c.execute("SELECT * FROM product WHERE product_id LIKE ? OR name LIKE ?", 
                            ('%' + search_term + '%', '%' + search_term + '%'))
                else:
                    c.execute("SELECT * FROM product")

                products = c.fetchall()
                products.sort(key=lambda x: x[0])
                if not products:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบสินค้าที่ค้นหา")
                else:
                    for product in products: #เป็นตัวโชขึันมาตามลำดับ
                        # product = (product_id, name, category, stock, price, manufacture_date, expiry_date, supplier, image_path)
                        status = determine_status(product[3], product[6])  # ใช้ stock และ expiry_date
                        tree.insert("", "end", values=(
                            product[0],  # product_id
                            product[1],  # name
                            product[2],  # category
                            product[3],  # stock
                            product[4],  # price
                            product[5],  # manufacture_date
                            product[6],  # expiry_date
                            product[7],  # supplier
                            status      # สถานะ
                        ))

            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

        # แสดงรายการสินค้าทันที เมื่อเปิดหน้าต่างจะแสดงทันที
        show_product()
        # ปุ่มค้นหา
        btn_search = Button(frame_input, text="ค้นหา", command=show_product, font=("Inter SemiBold", 15), 
                            bg="#5C7FCB", fg="#FFFFFF", padx=10, pady=2)
        btn_search.grid(row=0, column=2, padx=10)

        # ปุ่มปิดหน้าต่าง
        btn_close = Button(frame_input, text="ปิดหน้าต่าง", command=show_root.destroy, font=("Inter SemiBold", 15), 
                        bg="#FF5C5C", fg="#FFFFFF", padx=10, pady=2)
        btn_close.grid(row=0, column=3, padx=10)

##########################################################################
    #หน้าต่างเพิ่ม
    def open_add():
        global add_root
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if add_root is not None and add_root.winfo_exists():
            add_root.destroy()
            
        add_root = Toplevel(root)
        add_root.title("เพิ่มสินค้า") 
        add_root.geometry("1239x506+10+206")
        add_root.configure(background="#8FB1E0")

        # แถบด้านบน
        add_canvas = Canvas(add_root, bg="#5C7FCB", height=60, highlightthickness=0, relief="ridge")
        add_canvas.grid(row=0, column=0, columnspan=2, sticky="ew")
        add_canvas.create_text(10, 20, anchor="nw", text="เพิ่มสินค้าใหม่", fill="#FFFFFF", font=("Inter SemiBold", 20))

        # กำหนดการยืดของคอลัมน์
        add_root.columnconfigure(0, weight=1)
        add_root.rowconfigure(2, weight=1)
        
        # กำหนด Frame สำหรับช่องกรอก
        form_frame = Frame(add_root, bg="#8FB1E0")
        form_frame.grid(row=1, column=0, sticky="w")


        # กำหนด Label และ Entry สำหรับแต่ละฟิลด์ โดยใช้ grid()
        label_1 = Label(form_frame, text="รหัสสินค้า :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_1.grid(row=0, column=0, padx=5, pady=10)
        entry_id = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
        entry_id.grid(row=0, column=1, pady=10)

        label_2 = Label(form_frame, text="ชื่อยา :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_2.grid(row=1, column=0, padx=5, pady=10)
        entry_name = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
        entry_name.grid(row=1, column=1,pady=10)

        label_3 = Label(form_frame, text="รูปแบบ :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_3.grid(row=2, column=0, padx=5, pady=10)
        entry_category = ttk.Combobox(
            form_frame,
            values=["ยาเม็ด", "ยาแคปซูล", "ยาน้ำ", "ยาฉีด", "ยาทาภายนอก",
                    "ยาสูดดม", "ยาสำหรับสอดใส่","ยาผง","ยาผงฟู่",
                    "แผ่นแปะยา"],
            foreground="#5C7FCB",
            font=("Inter SemiBold", 13),
            width=25,
            state="normal"
        )
        entry_category.grid(row=2, column=1, pady=10)
        
        label_4 = Label(form_frame, text="จำนวนสต็อก :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_4.grid(row=3, column=0, padx=5, pady=10)
        entry_stock = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
        entry_stock.grid(row=3, column=1, pady=10)

        label_5 = Label(form_frame, text="ราคา :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_5.grid(row=0, column=2, padx=5, pady=10)
        entry_price = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
        entry_price.grid(row=0, column=3, pady=10)

        label_6 = Label(form_frame, text="วันที่ผลิต :", font=("Inter SemiBold", 17), background="#8FB1E0")
        label_6.grid(row=1, column=2, padx=5, pady=10)
        entry_manu = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB", font=("Inter SemiBold", 16))
        entry_manu.grid(row=1, column=3, pady=10)
        entry_manu.insert(0, "dd/mm/yyyy")

        label_7 = Label(form_frame, text="วันหมดอายุ :", font=("Inter SemiBold", 17), background="#8FB1E0")
        label_7.grid(row=2, column=2, padx=5, pady=10)
        entry_expi = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB", font=("Inter SemiBold", 16))
        entry_expi.grid(row=2, column=3, pady=10)
        entry_expi.insert(0, "dd/mm/yyyy")

        label_8 = Label(form_frame, text="บริษัทนำเข้ายา :",font=("Inter SemiBold", 17),background="#8FB1E0")
        label_8.grid(row=3, column=2, padx=5, pady=10)
        style.configure("TCombobox",fieldbackground="#EBF8FE",background="#5275C7",arrowcolor="#FFED23" )
        entry_supplier = ttk.Combobox(
            form_frame,
            values=["บริษัทโนวาร์ตีส(ประเทศไทย)จำกัด","บริษัทดีเคเอสเอช(ประเทศไทย)จำกัด","บริษัทซาโนฟี่-อเวนตีส(ประเทศไทย)จำกัด",
                    "บริษัท แกล็กโซสมิทไคล์น(ประเทศไทย)จำกัด","องค์การเภสัชกรรม(GPO)","บริษัทสยามเภสัชจำกัด",
                    "บริษัทโอลิค(ประเทศไทย)จำกัด","บริษัทอินเตอร์ไทยฟาร์มาซูติเคิ้ล แมนูแฟคเจอริ่งจำกัด)"],
            foreground="#5C7FCB",
            font=("Inter SemiBold", 13),  # ตั้งขนาดฟอนต์
            width=25,           # กำหนดความกว้าง          
            state="normal"      # อนุญาตให้พิมพ์ได้ 
    )
        entry_supplier.grid(row=3, column=3, pady=10)

        def pick_date(entry): 
            def grab_date():
                entry.delete(0, END)
                entry.insert(0, cal.get_date())
                date_window.destroy()

            date_window = Toplevel(add_root)
            date_window.grab_set()
            date_window.title("เลือกวันที่")
            date_window.geometry("343x337+590+370")
            cal = Calendar(date_window, selectmode="day", date_pattern="dd/mm/yyyy")
            cal.pack(pady=10)
            submit_btn = Button(date_window, text="เลือก", command=grab_date)
            submit_btn.pack()

        entry_manu.bind("<1>", lambda event: pick_date(entry_manu)) 
        entry_expi.bind("<1>", lambda event: pick_date(entry_expi)) #กดช่องวันต่างๆแล้วเรียกปฏิทินขึ้นมา

        def setPreviewPic(filepath):
            global img
            img = Image.open(filepath)
            img = img.resize((303, 320), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(img)
            show_pic.config(image=img)
            pathEntry.delete(0, END)
            pathEntry.insert(0, filepath)

        def selectPic():#กดให้เลือกรูป
            add_root.grab_set()
            global filename
            filename = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Select Image",
                filetypes=(("PNG Images", "*.png"), ("JPEG Images", "*.jpg;*.jpeg"))
            )
            if filename: #เรียกเดฟด้านบนขึ้นมา
                setPreviewPic(filename)
            add_root.grab_release() 
            
        def savePic():
            if not filename:
                tkinter.messagebox.showwarning("คำเตือน", "ไม่มีไฟล์ที่เลือก")
                return
            save_directory = r"C:\Users\chanan\Pictures\Img" 
            new_file_path = os.path.join(save_directory, os.path.basename(filename)) # ถ้ามีรูปจะเอามาเก็บในไฟล์นี้
            try:
                shutil.copy(filename, new_file_path)
            except Exception as e:
                tkinter.messagebox.showerror("คำเตือน", f"อัพโหลดไฟล์ไม่ได้: {e}")

        frame_img = Frame(add_root, bg="#8FB1E0")
        frame_img.place(x=858, y=76)

        selectBtn = customtkinter.CTkButton(frame_img, text="Browse Image", width=50, command=selectPic)
        pathEntry = customtkinter.CTkEntry(frame_img, width=200)
        show_pic = Label(frame_img)

        setPreviewPic(r"C:\Users\chanan\Pictures\Img\login\build\assets\frame0\image_1.png") #เป็นการเซ็ตรูปให้กลับไปเป็นตอนที่ยังไมไ่ด้ใส่รูป

        selectBtn.grid(row=0, column=0, padx=10, pady=5, ipady=0, sticky="e")
        pathEntry.grid(row=0, column=1, padx=10, pady=5, ipady=0, sticky="e")
        show_pic.grid(row=1, column=0, columnspan=3, pady=5, ipady=0, sticky="nswe")

        def save_product(image_path): # ทั้งก้อนจะเป็นการบันทึกข้อมูล
            product_id = entry_id.get()
            name = entry_name.get()
            category = entry_category.get()
            stock = int(entry_stock.get())
            price = float(entry_price.get())
            manufacture_date = entry_manu.get()
            expiry_date = entry_expi.get()
            supplier = entry_supplier.get()
            
            try:
                if stock < 0:
                    tkinter.messagebox.showinfo("คำเตือน", "จำนวนสต็อกต้องไม่ติดลบ")
                    return
                stock = int(stock)
            except ValueError:
                tkinter.messagebox.showerror("ข้อผิดพลาด", "จำนวนสต็อกต้องเป็นตัวเลข")
                return

            try: # เพิ่มข้อมูลในดาต้า
                c.execute('''INSERT INTO product (product_id, name, category, stock, price, manufacture_date, expiry_date, supplier, image_path)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (product_id, name, category, stock, price, manufacture_date, expiry_date, supplier, image_path))
                conn.commit()
                entry_id.delete(0, END)
                entry_name.delete(0, END)
                entry_category.set('')
                entry_stock.delete(0, END)
                entry_price.delete(0, END)
                entry_manu.delete(0, END)
                entry_manu.insert(0, "dd/mm/yyyy")
                entry_expi.delete(0, END)
                entry_expi.insert(0, "dd/mm/yyyy")
                entry_supplier.set('')

                #เป็นการเซ็ตค่ากลีบไปเป็นว่าง
                setPreviewPic(r"C:\Users\chanan\Pictures\Img\login\build\assets\frame0\image_1.png")
                tkinter.messagebox.showinfo("สำเร็จ", f"เพิ่มสินค้า '{name}' เรียบร้อยแล้ว!")
                add_root.lift()
                add_root.focus_force()
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", str(e))

        btn_save = Button(form_frame, text="บันทึก", command=lambda:[save_product(filename),savePic()], font=("Inter SemiBold", 13), bg="#5C7FCB", fg="#FFFFFF")
        btn_save.grid(row=6, column=2, padx=10, pady=10)

        btn_close = Button(form_frame, text="ปิดหน้าต่าง", command=add_root.destroy, font=("Inter SemiBold", 13), bg="#FF5C5C", fg="#FFFFFF")
        btn_close.grid(row=6, column=1, padx=10, pady=10)

##########################################################################

    def open_remove():
        global remove_root
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if remove_root is not None and remove_root.winfo_exists():
            remove_root.destroy()
            
        remove_root = Toplevel()
        remove_root.title("ลบสินค้า")
        remove_root.geometry("1239x506+10+206")
        remove_root.configure(background="#8FB1E0")
        remove_root.grab_set()

        show_canvas = Canvas(remove_root, bg="#5C7FCB", height=60, highlightthickness=0, relief="ridge")
        show_canvas.place(x=0, y=0,width=1290, height=70)
        show_canvas.create_text(10, 20, anchor="nw", text="ลบสินค้า", fill="#FFFFFF", font=("Inter SemiBold", 25))

        try:
            conn = sqlite3.connect(r"C:\Users\chanan\Desktop\Drug stock\ya.db")
            c = conn.cursor()
        except sqlite3.Error as e:
            tkinter.messagebox.showerror("คำเตือน", f"ไม่สามารถเชื่อมต่อญานข้อมูลได้: {e}")
            return

        # สร้าง Frame สำหรับ Treeview
        tree_frame = Frame(remove_root, bg="#8FB1E0")
        tree_frame.place(x=4, y=130)

        tree_frame.columnconfigure(0, weight=1)  # ทำให้ Treeview ขยายตามคอลัมน์ที่ 0
        tree_frame.columnconfigure(1, weight=0)  # ทำให้ Scrollbar มีความกว้างคงที่

        # สร้าง Treeview
        tree = ttk.Treeview(tree_frame, columns=("product_id", "name", "category", "stock", "price", "manufacture_date", "expiry_date", "supplier", "status"), 
                            show="headings", height=10, style="Custom.Treeview")

        tree.heading("product_id", text="รหัสสินค้า")
        tree.heading("name", text="ชื่อยา")
        tree.heading("category", text="รูปแบบ")
        tree.heading("stock", text="จำนวน")
        tree.heading("price", text="ราคา")
        tree.heading("manufacture_date", text="วันที่ผลิต")
        tree.heading("expiry_date", text="วันหมดอายุ")
        tree.heading("supplier", text="ผู้จัดจำหน่าย")
        tree.heading("status", text="สถานะ")

        tree.column("product_id", width=80)
        tree.column("name", width=200)
        tree.column("category", width=175)
        tree.column("stock", width=90)
        tree.column("price", width=90)
        tree.column("manufacture_date", width=100)
        tree.column("expiry_date", width=100)
        tree.column("supplier", width=200)
        tree.column("status", width=179)
        tree.grid(row=0, column=0, sticky="nsew")
        
        # เพิ่ม Scrollbar แนวตั้ง
        tree_scroll_y = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=tree_scroll_y.set)
        
        def show_product(): #เอาไว้แสดงรายการสินค้า
            tree.delete(*tree.get_children())
            product_id = product_id_entry.get().strip()

            try: #การค้นหาข้อมูลในฐานข้อมูล
                if product_id:
                    c.execute("SELECT * FROM product WHERE product_id LIKE ? OR name LIKE ?", 
                            ('%' + product_id + '%', '%' + product_id_entry + '%'))
                else:
                    c.execute("SELECT * FROM product")

                products = c.fetchall()
                products.sort(key=lambda x: x[0]) #เรียงลำดับข้อมูล
                if not products:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบสินค้าที่ค้นหา")
                else:
                    for product in products: #ถ้าเห็นจะแสดงข้อมูลตามลำดับ
                        status = determine_status(product[3], product[6])  # ใช้ stock และ expiry_date
                        tree.insert("", "end", values=(
                            product[0],  # product_id
                            product[1],  # name
                            product[2],  # category
                            product[3],  # stock
                            product[4],  # price
                            product[5],  # manufacture_date
                            product[6],  # expiry_date
                            product[7],  # supplier
                            status      # สถานะ
                        ))
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

        def delete_product():
            product_id = product_id_entry.get().strip() # ค่าที่พิมพ์ที่เข้ามา

            if not product_id: #ดูว่าได้กดไหม
                selected_item = tree.selection()
                if selected_item:
                    product_id = tree.item(selected_item, "values")[0]

            if product_id:
                try:
                    c.execute("SELECT * FROM product WHERE product_id = ?", (product_id,))
                    result = c.fetchone()
                    if result:
                        if tkinter.messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบ '{result[1]}' ใช่ไหม?"):
                            c.execute("DELETE FROM product WHERE product_id = ?", (product_id,))
                            conn.commit()
                            product_id_entry.delete(0, "end")
                            show_product()
                            tkinter.messagebox.showinfo("สำเร็จ", f"ลบสินค้า '{result[1]}' เรียบร้อยแล้ว!")
                    else:
                        tkinter.messagebox.showerror("คำเตือน", "ไม่พบสินค้าที่ต้องการลบ!")
                except sqlite3.Error as e:
                    tkinter.messagebox.showerror("คำเตือน", f"ไม่สามารถลบสินค้าได้: {e}")
            else:
                tkinter.messagebox.showwarning("คำเตือน", "กรุณาเลือกรหัสสินค้าหรือเลือกสินค้าจากตาราง")
        
        Label(remove_root, text="กรุณากรอกรหัสยาหรือเลือกยาที่ต้องการลบ:", font=("Inter", 17), bg="#8FB1E0").place(x=177, y=81)
        product_id_entry = Entry(remove_root, font=("Inter", 14), bg="#EBF8FE", fg="#5C7FCB")
        product_id_entry.place(x=588, y=87)

        show_product() #เรียกโชรายการทั้งหมดตอนที่เด่งหน้าต่าง
        
        button_frame = Frame(remove_root, bg="#8FB1E0")
        button_frame.place(x=850, y=82)

        btn_delete = Button(button_frame, text="ลบสินค้า", command=delete_product, font=("Inter", 14), bg="#5C7FCB", fg="#FFFFFF")
        btn_delete.grid(row=0,column=0)
        btn_close = Button(button_frame, text="ปิดหน้าต่าง", command=remove_root.destroy, font=("Inter", 14), bg="#FF5C5C", fg="#FFFFFF")
        btn_close.grid(row=0,column=1)


##########################################################################
    def open_update():
        global update_root
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if update_root is not None and update_root.winfo_exists():
            update_root.destroy()
            
        update_root = Toplevel(root)
        update_root.title("อัปเดตสินค้า")
        update_root.geometry("1239x506+10+206")
        update_root.configure(background="#8FB1E0")

        # ส่วนหัว
        update_canvas = Canvas(update_root, bg="#5C7FCB", height=60, highlightthickness=0, relief="ridge")
        update_canvas.place(x=0, y=0,width=1290, height=70)
        update_canvas.create_text(10, 20, anchor="nw", text="อัพเดทสินค้า", fill="#FFFFFF", font=("Inter SemiBold", 25))

        tree_frame = Frame(update_root, bg="#8FB1E0")
        tree_frame.place(x=0, y=130, relwidth=1, height=400)

        # สร้าง Treeview
        tree = ttk.Treeview(tree_frame, columns=("product_id", "name", "category", "stock", "price", "manufacture_date", "expiry_date", "supplier", "status"), 
                                show="headings", style="Custom.Treeview")
        
        tree.heading("product_id", text="รหัสสินค้า")
        tree.heading("name", text="ชื่อยา") 
        tree.heading("category", text="รูปแบบ")
        tree.heading("stock", text="จำนวน")
        tree.heading("price", text="ราคา")
        tree.heading("manufacture_date", text="วันที่ผลิต")
        tree.heading("expiry_date", text="วันหมดอายุ")
        tree.heading("supplier", text="บริษัทนำเข้ายา")
        tree.heading("status", text="สถานะ")

        tree.column("product_id", width=80)
        tree.column("name", width=200)
        tree.column("category", width=175)
        tree.column("stock", width=90)
        tree.column("price", width=90)
        tree.column("manufacture_date", width=100)
        tree.column("expiry_date", width=100)
        tree.column("supplier", width=200)
        tree.column("status", width=179)
        # ปรับตำแหน่ง Treeview
        tree.grid(row=0, column=0, sticky="nsew")
        tree_frame.grid_rowconfigure(0, weight=1)  # ทำให้แถวที่ 0 ขยายตามขนาด
        tree_frame.grid_columnconfigure(0, weight=1)  # ทำให้คอลัมน์ที่ 0 ขยายตามขนาด
        
        # เพิ่ม Scrollbar แนวตั้ง
        tree_scroll_y = Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree_scroll_y.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=tree_scroll_y.set)
        
        search_label = Label(update_root, text="กรอกรหัสสินค้า:", font=("Helvetica", 20), bg="#8FB1E0")
        search_label.place(x=204,y=77)
        search_entry = Entry(update_root, foreground="#5C7FCB",font=("Inter SemiBold", 16))
        search_entry.place(x=460,y=86)
        
        def load_products():
            tree.config(height=20)
            tree_frame.place(x=0, y=130, relwidth=1, height=400)
            tree.delete(*tree.get_children())
            search_term = search_entry.get().strip()

            try:
                if search_term:
                    c.execute("SELECT * FROM product WHERE product_id LIKE ? OR name LIKE ?", 
                            ('%' + search_term + '%', '%' + search_term + '%'))
                else:
                    c.execute("SELECT * FROM product")

                products = c.fetchall()
                products.sort(key=lambda x: x[0])
                
                if not products:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบสินค้าที่ค้นหา")
                else:
                    for product in products:
                        # product = (product_id, name, category, stock, price, manufacture_date, expiry_date, supplier, image_path)
                        status = determine_status(product[3], product[6])  # ใช้ stock และ expiry_date
                        tree.insert("", "end", values=(
                            product[0],  # product_id
                            product[1],  # name
                            product[2],  # category
                            product[3],  # stock
                            product[4],  # price
                            product[5],  # manufacture_date
                            product[6],  # expiry_date
                            product[7],  # supplier
                            status      # สถานะ
                        ))
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")
        
        def show_product():
            tree.delete(*tree.get_children())
            search_term = search_entry.get().strip()

            try:
                if search_term:
                    c.execute("SELECT * FROM product WHERE product_id LIKE ? OR name LIKE ?", 
                            ('%' + search_term + '%', '%' + search_term + '%'))
    
                products = c.fetchall()
                products.sort(key=lambda x: x[0])
                if not products:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบสินค้าที่ค้นหา")
                    return

                for product in products:
                    status = determine_status(product[3], product[6])  # ใช้ stock และ expiry_date
                    tree.insert("", "end", values=(
                        product[0],  # product_id
                        product[1],  # name
                        product[2],  # category
                        product[3],  # stock
                        product[4],  # price
                        product[5],  # manufacture_date
                        product[6],  # expiry_date
                        product[7],  # supplier
                        status      # สถานะ
                    ))

                tree.config(height=1)
                tree_frame.place(x=0, y=130, relwidth=1, height=66)
                tree_scroll_y.grid_forget()
                tree.update_idletasks()

                form_frame = Frame(update_root, bg="#8FB1E0")
                form_frame.place(x=32,y=220,width=1170)

                label_2 = Label(form_frame, text="ชื่อยา :",font=("Inter SemiBold", 16),background="#8FB1E0")
                label_2.grid(row=0, column=0, padx=10, pady=10, sticky="e")
                entry_name = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16), width=20)
                entry_name.grid(row=0, column=1, padx=10, pady=10)

                label_3 = Label(form_frame, text="รูปแบบ :",font=("Inter SemiBold", 16),background="#8FB1E0")
                label_3.grid(row=1, column=0, padx=10, pady=10, sticky="e")
                entry_category = ttk.Combobox(
                form_frame,
                values=["ยาเม็ด", "ยาแคปซูล", "ยาน้ำ", "ยาฉีด",
                        "ยาทาภายนอก ", "ยาสูดดม", "ยาสำหรับสอดใส่",
                        "ยาผง","ยาผงฟู่","แผ่นแปะยา"],
                foreground="#5C7FCB"
                ,font=("Inter SemiBold", 16),  # ตั้งขนาดฟอนต์
                width=19,           # กำหนดความกว้าง
                state="normal"      # อนุญาตให้พิมพ์ได้
                )
                entry_category.grid(row=1, column=1, padx=10, pady=10)
                        
                label_4 = Label(form_frame, text="จำนวนสต็อก :",font=("Inter SemiBold", 16),background="#8FB1E0")
                label_4.grid(row=2, column=0, padx=10, pady=10, sticky="e")
                entry_stock = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
                entry_stock.grid(row=2, column=1, padx=10, pady=10)

                label_5 = Label(form_frame, text="ราคา :",font=("Inter SemiBold", 16),background="#8FB1E0")
                label_5.grid(row=3, column=0, padx=10, pady=10, sticky="e")
                entry_price = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB",font=("Inter SemiBold", 16))
                entry_price.grid(row=3, column=1, padx=10, pady=10, sticky="e")

                label_6 = Label(form_frame, text="วันที่ผลิต :", font=("Inter SemiBold", 16), background="#8FB1E0")
                label_6.grid(row=0, column=3, padx=10, pady=10, sticky="e")
                entry_manu = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB", font=("Inter SemiBold", 16))                        
                entry_manu.grid(row=0, column=4, padx=10, pady=10)
                entry_manu.insert(0, product[5])

                label_7 = Label(form_frame, text="วันหมดอายุ :", font=("Inter SemiBold", 16), background="#8FB1E0")
                label_7.grid(row=1, column=3, padx=10, pady=10, sticky="e")
                entry_expi = Entry(form_frame, background="#EBF8FE", foreground="#5C7FCB", font=("Inter SemiBold", 16))
                entry_expi.grid(row=1, column=4, padx=10, pady=10)
                entry_expi.insert(0, product[6])

                label_8 = Label(form_frame, text="ผู้จัดจำหน่าย :",font=("Inter SemiBold", 16),background="#8FB1E0")
                label_8.grid(row=2, column=3, padx=10, pady=10, sticky="e")
                style.configure("TCombobox",fieldbackground="#EBF8FE",background="#5275C7",arrowcolor="#FFED23" )
                entry_supplier = ttk.Combobox(
                    form_frame,
                    values=["บริษัทโนวาร์ตีส(ประเทศไทย)จำกัด","บริษัทดีเคเอสเอช(ประเทศไทย)จำกัด","บริษัทซาโนฟี่-อเวนตีส(ประเทศไทย)จำกัด",
                    "บริษัท แกล็กโซสมิทไคล์น(ประเทศไทย)จำกัด","องค์การเภสัชกรรม(GPO)","บริษัทสยามเภสัชจำกัด",
                    "บริษัทโอลิค(ประเทศไทย)จำกัด","บริษัทอินเตอร์ไทยฟาร์มาซูติเคิ้ล แมนูแฟคเจอริ่งจำกัด)"],
                    foreground="#5C7FCB"
                    ,font=("Inter SemiBold", 16),  # ตั้งขนาดฟอนต์
                    width=19,           # กำหนดความกว้าง
                    state="normal"      # อนุญาตให้พิมพ์ได้ 
                )
                entry_supplier.grid(row=2, column=4, padx=10, pady=10)

                def setPreviewPic(filepath):
                    global img
                    try:
                        img = Image.open(filepath)
                        img = img.resize((285, 266), Image.Resampling.LANCZOS)
                        img = ImageTk.PhotoImage(img)
                        show_pic.config(image=img)
                        show_pic.image = img 
                        pathEntry.delete(0, END)
                        pathEntry.insert(0, filepath)
                    except Exception as e:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงภาพได้: {e}")

                def selectPic():
                    update_root.grab_set()
                    global filename
                    filename = filedialog.askopenfilename(
                        initialdir=os.getcwd(),
                        title="Select Image",
                        filetypes=(("PNG Images", "*.png"), ("JPEG Images", "*.jpg;*.jpeg"))
                    )
                    if filename:
                        setPreviewPic(filename)
                    update_root.grab_release() 
                    
                def savePic(image_path):
                    if not image_path:
                        tkinter.messagebox.showwarning("คำเตือน", "ไม่มีไฟล์ที่เลือก")
                        return None
                    save_directory = r"C:\Users\chanan\Pictures\Img"
                    new_file_path = os.path.join(save_directory, os.path.basename(image_path))
                    try:
                        shutil.copy(image_path, new_file_path)
                        return new_file_path
                    except Exception as e:
                        tkinter.messagebox.showerror("คำเตือน", f"ไม่สามารถอัปโหลดรูปได้: {e}")
                        return None
                    
                frame_img = Frame(update_root, bg="#8FB1E0")
                frame_img.place(x=890, y=205)

                selectBtn = customtkinter.CTkButton(frame_img, text="Browse Image", width=50, command=selectPic)
                selectBtn.grid(row=0, column=0, padx=10, pady=5, ipady=0, sticky="e")
                        
                pathEntry = customtkinter.CTkEntry(frame_img, width=200)
                pathEntry.grid(row=0, column=1, padx=10, pady=5, ipady=0, sticky="e")
                        
                show_pic = Label(update_root)
                show_pic.place(x=915, y=244)
                        
                setPreviewPic(product[8])

                def pick_date(entry):
                    def grab_date():
                        entry.delete(0, END)
                        entry.insert(0, cal.get_date())
                        date_window.destroy()

                    date_window = Toplevel(update_root)
                    date_window.grab_set()
                    date_window.title("เลือกวันที่")
                    date_window.geometry("343x337+590+370")
                    cal = Calendar(date_window, selectmode="day", date_pattern="dd/mm/yyyy")
                    cal.pack(pady=10)
                    submit_btn = Button(date_window, text="เลือก", command=grab_date, width=10, height=2)
                    submit_btn.pack()

                entry_manu.bind("<1>", lambda event: pick_date(entry_manu))
                entry_expi.bind("<1>", lambda event: pick_date(entry_expi))

                filename = None
                def update_product(image_path):
                    product_id = search_entry.get().strip()

                    if not product_id:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกรหัสสินค้าก่อน")
                        return

                    # สร้างรายการฟิลด์และค่าที่จะอัปเดต
                    update_fields = []
                    update_values = []

                    name = entry_name.get().strip()
                    if name:
                        update_fields.append("name=?") #เพิ่มข้อความ "name=?" เข้าไปใน update_fields
                        update_values.append(name) #เพิ่มข้อความ "name" เข้าไปใน update_values

                    category = entry_category.get().strip()
                    if category:
                        update_fields.append("category=?")
                        update_values.append(category)

                    stock = entry_stock.get().strip()
                    if stock:
                        try:
                            stock = int(stock)
                            if stock < 0:
                                tkinter.messagebox.showinfo("คำเตือน", "จำนวนสต็อกต้องมากกว่า 0")
                                return
                            update_fields.append("stock=?")
                            update_values.append(stock)
                        except ValueError:
                            tkinter.messagebox.showerror("ข้อผิดพลาด", "จำนวนสต็อกต้องเป็นตัวเลข")
                            return

                    price = entry_price.get().strip()
                    if price:
                        try:
                            price = float(price)
                            update_fields.append("price=?")
                            update_values.append(price)
                        except ValueError:
                            tkinter.messagebox.showerror("ข้อผิดพลาด", "ราคาต้องเป็นตัวเลข")
                            return

                    manufacture_date = entry_manu.get().strip()
                    if manufacture_date:
                        update_fields.append("manufacture_date=?")
                        update_values.append(manufacture_date)

                    expiry_date = entry_expi.get().strip()
                    if expiry_date:
                        update_fields.append("expiry_date=?")
                        update_values.append(expiry_date)

                    supplier = entry_supplier.get().strip()
                    if supplier:
                        update_fields.append("supplier=?")
                        update_values.append(supplier)

                    if not image_path:
                        image_path = product[8]
                    else:
                        new_path = savePic(image_path)
                        if new_path:
                            update_fields.append("image_path=?")
                            update_values.append(new_path)

                    if not update_fields:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกข้อมูลอย่างน้อยหนึ่งช่องเพื่ออัปเดต")
                        return

                    update_fields_str = ", ".join(update_fields)
                    update_values.append(product_id)

                    try:
                        query = f"""UPDATE product SET {update_fields_str} WHERE product_id=?"""
                        c.execute(query, tuple(update_values))
                        conn.commit()
                        update_root.grab_set()
                        tkinter.messagebox.showinfo("สำเร็จ", "ข้อมูลสินค้าได้รับการอัปเดตแล้ว")
                    except sqlite3.Error as e:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถอัปเดตข้อมูลได้: {e}")
                
                def backform():
                    search_entry.delete(0, END)
                    form_frame.place_forget()
                    update_button.place_forget()
                    frame_img.place_forget()
                    show_pic.place_forget()
                    load_products()
                              
                update_button = Button(update_root, text="บันทึกข้อมูล", font=("Inter SemiBold", 15), bg="#5C7FCB", fg="#FFFFFF", width=10, height=1, command=lambda:[update_product(filename)])
                update_button.place(x=440,y=460)
                back_button = Button(update_root, text="กลับ", bg="#5C7FCB", fg="#FFFFFF", font=("Inter SemiBold", 15), width=10, height=1, command=lambda:[load_products(),backform()])
                back_button.place(x=1073, y=17)
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")
                    
        search_button = Button(update_root, text="ค้นหา",bg="#5C7FCB", fg="#FFFFFF",font=("Inter SemiBold", 15), width=10, height=1, command=show_product)
        search_button.place(x=722,y=79)
        dele_button = Button(update_root, text="ปิดหน้าต่าง", bg="#FF5C5C", fg="#FFFFFF",font=("Inter SemiBold", 15), width=10, height=1, command=update_root.destroy)
        dele_button.place(x=857,y=79)
        
        load_products()

##########################################################################
    def open_employees():
        global employees_root
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if employees_root is not None and employees_root.winfo_exists():
            employees_root.destroy()
            
        employees_root = Toplevel(root)
        employees_root.title("พนักงาน")
        employees_root.geometry("1239x506+10+206")
        employees_root.configure(background="#8FB1E0")
        
        if not current_user:
            tkinter.messagebox.showerror("ข้อผิดพลาด", "กรุณาเข้าสู่ระบบก่อน")
            return

        # ดึงข้อมูลพนักงานที่เข้าสู่ระบบ
        try:
            s.execute("SELECT * FROM users WHERE username = ?", (current_user[1],))
            employee = s.fetchone()
            if not employee:
                tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบข้อมูลพนักงาน")
                return
        except sqlite3.Error as e:
            tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")
            return
        
        # สร้าง Frame สำหรับข้อมูลพนักงาน
        employee_frame = Frame(employees_root, bg="#8FB1E0", padx=10, pady=10)
        employee_frame.place(x=25,y=14)

        label_username1 = Label(employee_frame, text="ชื่อผู้ใช้", font=("Arial", 14), bg="#8FB1E0")
        label_username1.grid(row=0, column=0, sticky="w", pady=5)
        entry_username1 = Label(employee_frame, text=employee[1], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_username1.grid(row=0, column=1, pady=5, padx=10)

        label_password1 = Label(employee_frame, text="รหัสผ่าน", font=("Arial", 14), bg="#8FB1E0")
        label_password1.grid(row=1, column=0, sticky="w", pady=5)
        entry_password1 = Label(employee_frame, text=employee[2], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_password1.grid(row=1, column=1, pady=5, padx=10)

        label_email1 = Label(employee_frame, text="อีเมล", font=("Arial", 14), bg="#8FB1E0")
        label_email1.grid(row=2, column=0, sticky="w", pady=5)
        entry_email1 = Label(employee_frame, text=employee[3], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_email1.grid(row=2, column=1, pady=5, padx=10)

        label_birthday1 = Label(employee_frame, text="วัน เดือน ปี เกิด", font=("Arial", 14), bg="#8FB1E0")
        label_birthday1.grid(row=3, column=0, sticky="w", pady=5)
        entry_birthday1 = Label(employee_frame, text=employee[4], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_birthday1.grid(row=3, column=1, pady=5, padx=10)

        label_id_card1 = Label(employee_frame, text="เลขบัตรประชาชน", font=("Arial", 14), bg="#8FB1E0")
        label_id_card1.grid(row=4, column=0, sticky="w", pady=5)
        entry_id_card1 = Label(employee_frame, text=employee[5], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_id_card1.grid(row=4, column=1, pady=5, padx=10)

        label_address1 = Label(employee_frame, text="ที่อยู่", font=("Arial", 14), bg="#8FB1E0")
        label_address1.grid(row=5, column=0, sticky="w", pady=5)
        entry_address1 = Label(employee_frame, text=employee[6], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_address1.grid(row=5, column=1, pady=5, padx=10)

        label_phone1 = Label(employee_frame, text="เบอร์โทรศัพท์", font=("Arial", 14), bg="#8FB1E0")
        label_phone1.grid(row=6, column=0, sticky="w", pady=5)
        entry_phone1 = Label(employee_frame, text=employee[7], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", width=40, anchor="w")
        entry_phone1.grid(row=6, column=1, pady=5, padx=10)

        label_position1 = Label(employee_frame, text="ตำแหน่ง", font=("Arial", 14), bg="#8FB1E0")
        label_position1.grid(row=7, column=0, sticky="w", pady=5)
        entry_position1 = Label(employee_frame, text=employee[9], font=("Inter SemiBold", 14), bg="white", fg="#5C7FCB", anchor="w")
        entry_position1.grid(row=7, column=1, pady=5, padx=10)
        
        def setPreviewPic(filepath):
            global img
            try:
                img = Image.open(filepath)
                img = img.resize((150, 250), Image.Resampling.LANCZOS)
                img = ImageTk.PhotoImage(img)
                show_pic.config(image=img)
                show_pic.image = img 
                pathEntry.delete(0, END)
                pathEntry.insert(0, filepath)
            except Exception as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงภาพได้: {e}")

        def selectPic():
            employees_root.grab_set()
            global filename
            filename = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Select Image",
                filetypes=(("PNG Images", "*.png"), ("JPEG Images", "*.jpg;*.jpeg"))
            )
            if filename:
                setPreviewPic(filename)
            employees_root.grab_release() 
                
        def savePic(image_path):
            if not image_path:
                tkinter.messagebox.showwarning("คำเตือน", "ไม่มีไฟล์ที่เลือก")
                return None

            # ตรวจสอบว่าไฟล์มีอยู่จริงและเป็นไฟล์รูปภาพที่ถูกต้อง
            if not os.path.isfile(image_path):
                tkinter.messagebox.showerror("ข้อผิดพลาด", "ไฟล์รูปภาพไม่ถูกต้องหรือไม่พบไฟล์")
                return None

            save_directory = r"C:\Users\chanan\Pictures\Img"
            os.makedirs(save_directory, exist_ok=True)

            # บันทึกรูปภาพไปยังโฟลเดอร์ที่กำหนด
            new_file_path = os.path.join(save_directory, os.path.basename(image_path))
            try:
                shutil.copy(image_path, new_file_path)  # คัดลอกรูปภาพไปยังตำแหน่งใหม่
                return new_file_path  # คืนค่าเส้นทางไฟล์ใหม่
            except Exception as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการบันทึกรูปภาพ: {e}")
                return None
        
        frame_img = Frame(employees_root, bg="#8FB1E0")
        frame_img.place(x=862, y=200)

        selectBtn = customtkinter.CTkButton(frame_img, text="Browse Image", width=50, command=selectPic)
        pathEntry = customtkinter.CTkEntry(frame_img, width=200)
        show_pic = Label(frame_img)

        setPreviewPic(employee[8])

        selectBtn.grid_forget()
        pathEntry.grid_forget()
        show_pic.grid(row=1, column=0, columnspan=3, pady=5, ipady=0, sticky="nswe")
        
        if current_user[9] == "เจ้าของร้าน":
            label_username1.grid_remove()
            entry_username1.grid_remove()

            label_password1.grid_remove()
            entry_password1.grid_remove()
            
            label_email1.grid_remove()
            entry_email1.grid_remove()

            label_birthday1.grid_remove()
            entry_birthday1.grid_remove()

            label_id_card1.grid_remove()
            entry_id_card1.grid_remove()

            label_address1.grid_remove()
            entry_address1.grid_remove()

            label_phone1.grid_remove()
            entry_phone1.grid_remove()

            label_position1.grid_remove()
            entry_position1.grid_remove()
            
            # สร้าง Frame สำหรับ Treeview
            employee_tree_frame = Frame(employees_root, bg="#8FB1E0", padx=10, pady=10,width=700, height=100)
            employee_tree_frame.place(x=24, y=204)

            # สร้าง Treeview
            employee_tree = ttk.Treeview(
                employee_tree_frame,
                columns=("username", "email", "phone", "role"),
                show="headings",
                height=5,  # ปรับความสูงของ Treeview
                style="Custom.Treeview"
            )

            # ตั้งค่าหัวคอลัมน์
            employee_tree.heading("username", text="ชื่อผู้ใช้")
            employee_tree.heading("email", text="อีเมล")
            employee_tree.heading("phone", text="เบอร์โทรศัพท์")
            employee_tree.heading("role", text="ตำแหน่ง")

            # ตั้งค่าคอลัมน์
            employee_tree.column("username", width=190, anchor="center")
            employee_tree.column("email", width=200, anchor="center")
            employee_tree.column("phone", width=190, anchor="center")
            employee_tree.column("role", width=150, anchor="center")

            # วาง Treeview ใน Grid
            employee_tree.grid(row=0, column=0, sticky="nsew")

            employee_tree_frame.grid_rowconfigure(0, weight=1)
            employee_tree_frame.grid_columnconfigure(0, weight=1)

            # เพิ่ม Scrollbar แนวตั้ง
            employee_tree_scroll_y = Scrollbar(employee_tree_frame, orient="vertical", command=employee_tree.yview)
            employee_tree_scroll_y.grid(row=0, column=1, sticky="ns")
            employee_tree.configure(yscrollcommand=employee_tree_scroll_y.set)
            
            label_position = Label(employee_frame, text="ตำแหน่ง", font=("Arial", 14), bg="#8FB1E0")
            label_position.grid(row=3, column=3, sticky="w", pady=5)
            style = ttk.Style()
            style.configure("TCombobox",fieldbackground="#8FB1E0",bd=0, highlightthickness=0,arrowcolor="#FFED23" )
            entry_position = ttk.Combobox(
                employee_frame,
                values=["เจ้าของร้าน","เจ้าหน้าที่สต๊อกสินค้า","เภสัชกร","ผู้ช่วยเภสัชกร(พนักงาน)"],
                foreground="#000000",
                font=("Inter SemiBold", 20),  # ตั้งขนาดฟอนต์
                height=7,
                width=14,           # กำหนดความกว้าง          
                state="normal"      # อนุญาตให้พิมพ์ได้ 
            )
            entry_position.insert(0, employee[9])
            entry_position.grid(row=3, column=4, pady=5, padx=10)
            
            label_username = Label(employee_frame, text="ชื่อผู้ใช้", font=("Arial", 14), bg="#8FB1E0")
            label_username.grid(row=0, column=0, sticky="w", pady=5)
            entry_username = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_username.grid(row=0, column=1, pady=5, padx=10)
            entry_username.insert(0, employee[1])
            
            label_password = Label(employee_frame, text="รหัสผ่าน", font=("Arial", 14), bg="#8FB1E0")
            label_password.grid(row=1, column=0, sticky="w", pady=5)
            entry_password = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_password.grid(row=1, column=1, pady=5, padx=10)
            entry_password.insert(0, employee[2])
            
            label_email = Label(employee_frame, text="อีเมล", font=("Arial", 14), bg="#8FB1E0")
            label_email.grid(row=2, column=0, sticky="w", pady=5)
            entry_email = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_email.grid(row=2, column=1, pady=5, padx=10)
            entry_email.insert(0, employee[3])
            
            label_birthday = Label(employee_frame, text="วัน เดือน ปี เกิด", font=("Arial", 14), bg="#8FB1E0")
            label_birthday.grid(row=3, column=0, sticky="w", pady=5)
            entry_birthday = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_birthday.grid(row=3, column=1, pady=5, padx=10)
            entry_birthday.insert(0, employee[4])
            
            label_id_card = Label(employee_frame, text="เลขบัตรประชาชน", font=("Arial", 14), bg="#8FB1E0")
            label_id_card.grid(row=0, column=3, sticky="w", pady=5)
            entry_id_card = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_id_card.grid(row=0, column=4, pady=5, padx=10)
            entry_id_card.insert(0, employee[5])

            label_address = Label(employee_frame, text="ที่อยู่", font=("Arial", 14), bg="#8FB1E0")
            entry_address = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_address.insert(0, employee[6])
            label_address.grid(row=1, column=3, sticky="w", pady=5)
            entry_address.grid(row=1, column=4, pady=5, padx=10)
            
            label_phone = Label(employee_frame, text="เบอร์โทรศัพท์", font=("Arial", 14), bg="#8FB1E0")
            entry_phone = Entry(employee_frame, foreground="#5C7FCB",font=("Inter SemiBold", 14), width=40)
            entry_phone.insert(0, employee[7])
            label_phone.grid(row=2, column=3, sticky="w", pady=5)
            entry_phone.grid(row=2, column=4, pady=5, padx=10)
                    
            frame_img = Frame(employees_root, bg="#8FB1E0")
            frame_img.place(x=941, y=290)
            selectBtn.grid(row=0, column=0, padx=10, pady=5, ipady=0, sticky="e")
            pathEntry.grid(row=0, column=1, padx=10, pady=5, ipady=0, sticky="e")
            
            # ดึงข้อมูลพนักงานทั้งหมดจากฐานข้อมูล
            try:
                s.execute("SELECT username, email, phone, role FROM users")
                employees = s.fetchall()
                for emp in employees:
                    employee_tree.insert("", "end", values=emp)
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

            # ฟังก์ชันเมื่อคลิกที่ Treeview
            def on_treeview_select(event):
                selected_item = employee_tree.selection()
                if selected_item:
                    emp_username = employee_tree.item(selected_item, "values")[0]
                    
                    try:
                        s.execute("SELECT * FROM users WHERE username = ?", (emp_username,))
                        emp_data = s.fetchone()
                        if emp_data:
                            entry_username.delete(0, END)
                            entry_username.insert(0, emp_data[1])
                            entry_password.delete(0, END)
                            entry_password.insert(0, emp_data[2])
                            entry_email.delete(0, END)
                            entry_email.insert(0, emp_data[3])
                            entry_birthday.delete(0, END)
                            entry_birthday.insert(0, emp_data[4])
                            entry_id_card.delete(0, END)
                            entry_id_card.insert(0, emp_data[5])
                            entry_address.delete(0, END)
                            entry_address.insert(0, emp_data[6])
                            entry_phone.delete(0, END)
                            entry_phone.insert(0, emp_data[7])
                            entry_position.set(emp_data[9])
                            setPreviewPic(emp_data[8])
                    except sqlite3.Error as e:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

            # ฟังก์ชันลบพนักงาน
            def delete_employee():
                selected_item = employee_tree.selection()
                if selected_item:
                    emp_username = employee_tree.item(selected_item, "values")[0]
                    
                    # การยืนยันก่อนลบ
                    confirm = tkinter.messagebox.askyesno("ยืนยันการลบ", f"คุณต้องการลบพนักงาน '{emp_username}' หรือไม่?")
                    if confirm:
                        try:
                            s.execute("DELETE FROM users WHERE username = ?", (emp_username,))
                            logins.commit()
                            tkinter.messagebox.showinfo("สำเร็จ", f"พนักงาน '{emp_username}' ถูกลบเรียบร้อยแล้ว")
                            
                        except sqlite3.Error as e:
                            tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการลบข้อมูล: {e}")
                else:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "กรุณาเลือกพนักงานที่ต้องการลบ")
                    
            delete_button = Button(employees_root, text="ลบพนักงาน", font=("Arial", 14), bg="#FF4C4C", fg="white", command=delete_employee)
            delete_button.place(x=370, y=445)
            
            # ผูกฟังก์ชันคลิกกับ Treeview
            employee_tree.bind("<ButtonRelease-1>", on_treeview_select)  

            def pick_date(entry):
                def grab_date():
                    entry.delete(0, END)
                    entry.insert(0, cal.get_date())
                    date_window.destroy()

                date_window = Toplevel(employees_root)
                date_window.grab_set()
                date_window.title("เลือกวันที่")
                date_window.geometry("343x337+590+370")
                cal = Calendar(date_window, selectmode="day", date_pattern="dd/mm/yyyy")
                cal.pack(pady=10)
                submit_btn = Button(date_window, text="เลือก", command=grab_date)
                submit_btn.pack()

            entry_birthday.bind("<1>", lambda event: pick_date(entry_birthday))

            # ฟังก์ชันบันทึกข้อมูล
            def save_changes(image_path):
                global current_user
                username = entry_username.get()
                password = entry_password.get()
                email = entry_email.get()
                birthday = entry_birthday.get()
                cardnumber = entry_id_card.get()
                address = entry_address.get()
                phone = entry_phone.get()
                position = entry_position.get()

                updated_fields = []
                updated_values = []

                # ตรวจสอบว่ามีการเลือกพนักงานใน Treeview หรือไม่
                if not employee_tree.selection():
                    tkinter.messagebox.showwarning("คำเตือน", "กรุณาเลือกพนักงานก่อนเปลี่ยนตำแหน่ง")
                    return

                # ดึง `username` เดิมของพนักงานที่ถูกเลือก
                selected_item = employee_tree.selection()[0]
                original_username = employee_tree.item(selected_item, "values")[0]

                # ดึงข้อมูลปัจจุบันจากฐานข้อมูลมาเปรียบเทียบ
                current_data_query = f"""
                    SELECT username, password, email, birthday, cardnumber, address, phone, role, image_path
                    FROM users
                    WHERE username = ?
                """
                s.execute(current_data_query, (original_username,))
                current_user_data = s.fetchone()

                # ตรวจสอบการเปลี่ยนแปลงแต่ละฟิลด์
                if current_user_data[0] != username and username != "":
                    updated_fields.append("username = ?")
                    updated_values.append(username)

                if current_user_data[1] != password and password != "":
                    updated_fields.append("password = ?")
                    updated_values.append(password)

                if current_user_data[2] != email and email != "":
                    updated_fields.append("email = ?")
                    updated_values.append(email)

                if current_user_data[3] != birthday and birthday != "":
                    updated_fields.append("birthday = ?")
                    updated_values.append(birthday)

                if current_user_data[4] != cardnumber and cardnumber != "":
                    updated_fields.append("cardnumber = ?")
                    updated_values.append(cardnumber)

                if current_user_data[5] != address and address != "":
                    updated_fields.append("address = ?")
                    updated_values.append(address)

                if current_user_data[6] != phone and phone != "":
                    updated_fields.append("phone = ?")
                    updated_values.append(phone)

                if current_user_data[7] != position and position != "":
                    updated_fields.append("role = ?")
                    updated_values.append(position)

                # กำหนดค่าเริ่มต้นให้กับ new_path
                new_path = None
                
                # จัดการอัปเดตรูปภาพ
                if image_path and image_path != current_user_data[8]:
                    new_path = savePic(image_path)  # บันทึกรูปภาพใหม่
                    if new_path:  # ถ้าบันทึกสำเร็จ
                        updated_fields.append("image_path = ?")
                        updated_values.append(new_path)
                else:
                    image_path = current_user_data[8]

                if updated_fields:
                    try:
                        # สร้างคำสั่ง SQL สำหรับการอัปเดต
                        set_clause = ", ".join(updated_fields)
                        sql_query = f"""
                            UPDATE users
                            SET {set_clause}
                            WHERE username = ?
                        """
                        updated_values.append(original_username)  # ใช้ `original_username` ระบุ record
                        s.execute(sql_query, tuple(updated_values))
                        logins.commit()
                        
                        # ตรวจสอบว่าผู้ใช้ที่เลือกตรงกับ current_user หรือไม่
                        if original_username == current_user[1] and username != "":
                            current_user = list(current_user)  # แปลงเป็น list
                            current_user[1] = username  # อัปเดต username
                            current_user = tuple(current_user)  # แปลงกลับเป็น tuple

                        tkinter.messagebox.showinfo("สำเร็จ", "ข้อมูลของพนักงานถูกอัปเดตสำเร็จ")
                        
                    except sqlite3.Error as e:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")
                else:
                    tkinter.messagebox.showinfo("ไม่มีการเปลี่ยนแปลง", "ไม่มีข้อมูลที่ถูกเปลี่ยนแปลง")

            # ปุ่มบันทึก
            save_button = Button(employees_root, text="บันทึก", font=("Arial", 14), bg="#5C7FCB", fg="white", command=lambda: [save_changes(pathEntry.get())])
            save_button.place(x=243,y=445)

##########################################################################
    def maker():
        global maker_root
        # หากมีหน้าต่างเปิดอยู่ให้ปิดก่อน
        if maker_root is not None and maker_root.winfo_exists():
            maker_root.destroy()

        maker_root = Toplevel(root)
        maker_root.title("ผู้จัดทำ")
        maker_root.geometry("1239x506+10+206")

        img = Image.open(r"C:\Users\chanan\Downloads\663050141-4.png")
        img = img.resize((1239, 506), Image.Resampling.LANCZOS)  # ปรับขนาดภาพให้พอดีกับหน้าต่าง
        bg_image = ImageTk.PhotoImage(img)  # แปลงให้เป็นรูปแบบที่ Tkinter รองรับ

        # เก็บตัวแปร bg_image ให้สามารถเข้าถึงได้ในภายหลัง
        background_label = Label(maker_root, image=bg_image)
        background_label.place(relwidth=1, relheight=1)
        background_label.image = bg_image
    
##########################################################################
    #ออกจากโปรแกรม
    def exit():
        confirm = tkinter.messagebox.askquestion("ยืนยันการออกจากโปรแกรม","คุณต้องการออกจากโปรแกรมหรือไม่")
        if confirm =="yes":
            root.withdraw()
            if show_root is not None and show_root.winfo_exists():
                show_root.destroy()
            if update_root is not None and update_root.winfo_exists():
                update_root.destroy()
            if add_root is not None and add_root.winfo_exists():
                add_root.destroy()
            if remove_root is not None and remove_root.winfo_exists():
                remove_root.destroy()
            if maker_root is not None and maker_root.winfo_exists():
                maker_root.destroy()
            if employees_root is not None and employees_root.winfo_exists():
                employees_root.destroy()
            loginwindow(root)
    
    #ปุ่มเมนู
    buttonmaker = PhotoImage(file=relative_to_assets("button_1.png"))  
    button_1 = Button(image=buttonmaker,borderwidth=0,highlightthickness=0,command=maker,relief="flat")
    button_1.place(x=960.0,y=92.0,width=199,height=65)
    
    buttonupdate = PhotoImage(file=relative_to_assets("button_2.png"))
    button_2 = Button(image=buttonupdate,borderwidth=0,highlightthickness=0,command=open_update,relief="flat")
    button_2.place(x=729.0,y=92.0,width=222,height=62)

    buttonremove = PhotoImage(file=relative_to_assets("button_3.png"))
    button_3 = Button(image=buttonremove,borderwidth=0,highlightthickness=0,command=open_remove,relief="flat")
    button_3.place(x=501.0,y=90.0,width=222,height=65)

    buttonadd = PhotoImage(
    file=relative_to_assets("button_4.png"))
    button_4 = Button(image=buttonadd,borderwidth=0,highlightthickness=0,command=open_add,relief="flat")
    button_4.place(x=282.0,y=90.0,width=213,height=68)

    buttonshow = PhotoImage(file=relative_to_assets("button_5.png"))
    button_5 = Button(image=buttonshow,borderwidth=0,highlightthickness=0,command=open_show,relief="flat")
    button_5.place(x=61.0,y=87.0,width=213,height=68)

    buttonexit = PhotoImage(file=relative_to_assets("button_6.png"))
    button_6 = Button(image=buttonexit,borderwidth=0,highlightthickness=0,command=exit,relief="flat")
    button_6.place(x=1191.0,y=632.0,width=46,height=52)
    
    buttonuser = PhotoImage(file=relative_to_assets(r"C:\Users\chanan\Desktop\build\assets\frame0\button_9.png"))
    button_8 = Button(image=buttonuser,borderwidth=0,highlightthickness=0,command=open_employees,relief="flat")
    button_8.place(x=1169.0,y=93.0,width=58.0,height=59.0)
    
    original_image = Image.open(relative_to_assets("image_1.png"))
    resized_image = original_image.resize((1248, 675))

    # แปลงภาพที่ปรับขนาดแล้วให้ใช้กับ Tkinter
    image_image_1 = ImageTk.PhotoImage(resized_image)
    image_1 = canvas.create_image(632,498,image=image_image_1)
    canvas.tag_lower(image_1)
    
    image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
    image_2 = canvas.create_image(90.0,48.0,image=image_image_2)

    image_image_3 = PhotoImage(file=relative_to_assets(r"C:\Users\chanan\Desktop\build\assets\frame0\image_3.png"))
    image_3 = canvas.create_image(950.0,52.0,image=image_image_3)
    
    btn_save_pdf = Button(root, text="Report", command=preview_report, font=("Inter SemiBold", 15), bg="#5C7FCB", fg="#FFFFFF", padx=10, pady=2)
    btn_save_pdf.place(x=501.0,y=250,width=222.0,height=65.0)

    root.mainloop()

##########################################################################

# ดึงที่อยู่ของฟอนต์ภาษาไทย
font_path = r"C:\Users\chanan\project\ChulaNarak Regular\ChulaNarak Regular.ttf"
pdfmetrics.registerFont(TTFont('ChulaNarak Regular', font_path)) #ลงทะเบียนฟอนฟอนต์ TrueType ให้กับ ReportLab ซึ่งเป็นไลบรารีสำหรับสร้างไฟล์ PDF

# ฟังก์ชันดึงข้อมูลจากฐานข้อมูล
def fetch_data(selected_supplier=None):
    conn = sqlite3.connect(r"C:\Users\chanan\Desktop\Drug stock\ya.db")
    c = conn.cursor()
    #ดึงรายการสินค้าที่มีสต็อกมากกว่า 0
    query = "SELECT product_id, name, category, stock, supplier FROM product WHERE stock > 0"
    if selected_supplier:
        query += f" AND supplier = '{selected_supplier}'" #ถ้าผู้ใช้ระบุ supplier, เพิ่มเงื่อนไขให้เลือกเฉพาะสินค้าของ supplier
    c.execute(query)
    products_in_stock = sorted(c.fetchall(), key=lambda x: x[0])
    #ดึงรายการสินค้าที่มีสต็อกต่ำกว่า 5
    query = "SELECT product_id, name, stock, supplier FROM product WHERE stock <= 5"
    if selected_supplier:
        query += f" AND supplier = '{selected_supplier}'" #ใช้เงื่อนไข supplier เหมือนกับขั้นตอนก่อนหน้า
    c.execute(query)
    low_stock_products = sorted(c.fetchall(), key=lambda x: x[0])
    #ดึงข้อมูลสรุปสต็อกสินค้าของแต่ละ supplier แยกตาม category
    query = "SELECT supplier, category, SUM(stock) FROM product GROUP BY supplier, category" #จัดกลุ่มข้อมูล
    if selected_supplier:
        query = f"SELECT supplier, category, SUM(stock) FROM product WHERE supplier = '{selected_supplier}' GROUP BY category"
    c.execute(query) #ถ้ามีการระบุ supplier, ให้ดึงเฉพาะสินค้าของ supplier นั้น
    supplier_summary = sorted(c.fetchall(), key=lambda x: x[0])

    c.execute("SELECT DISTINCT supplier FROM product") #ดึงรายการ supplier ที่มีสินค้าอยู่ โดยไม่เอาค่าซ้ำ
    suppliers = [row[0] for row in c.fetchall()] #แปลงข้อมูลเป็นรายการ (list) เฉพาะชื่อ supplier

    return products_in_stock, low_stock_products, supplier_summary, suppliers

# ฟังก์ชันแสดงรายงาน
def preview_report(): # กำหนดให้ตัวแปรเหล่านี้เป็น Global เพื่อให้สามารถเข้าถึงฟังชัน
    global check_var_stock, check_var_low, check_var_supplier, supplier_var

    products_in_stock, low_stock_products, supplier_summary, suppliers = fetch_data() #ดึงข้อมูลจากฐานข้อมูล

    preview_window = Toplevel(root)
    preview_window.title("รายงาน")
    preview_window.geometry("1239x506+10+206")

    notebook = ttk.Notebook(preview_window) #สร้าง Notebook สำหรับแสดงแท็บข้อมูล
    notebook.pack(expand=True, fill="both", padx=10, pady=10) #ขยายพื้นที่หน้าต่าง
    #สร้าง Dropdown สำหรับเลือกบริษัท
    supplier_var = StringVar() #เก็บค่าที่เลือกจาก Combobox
    supplier_var.set("ทั้งหมด") #ค่าเริ่มต้น

    supplier_frame = Frame(preview_window) #สร้าง Frame จัดกลุ่มการเลือกบริษัท
    supplier_frame.pack(fill="x", padx=10, pady=5) # ขยายเต็มแนวแกน x และเพิ่มระยะห่าง
    
    Label(supplier_frame, text="เลือกบริษัท:").pack(side="left") #เพื่อแสดงข้อความและ ให้ผู้ใช้เลือกบริษัทจาก suppliers
    supplier_dropdown = ttk.Combobox(supplier_frame, textvariable=supplier_var, values=["ทั้งหมด"] + suppliers, state="readonly")
    supplier_dropdown.pack(side="left", padx=10)
    Button(supplier_frame, text="ดูรายงาน", command=lambda: update_report(notebook)).pack(side="left") #สร้างปุ่ม

    # Checkbox ให้เลือกข้อมูลที่ต้องการพิมพ์
    check_var_stock = BooleanVar(value=True) #กำหนดค่าเริ่มต้น เป็น True
    check_var_low = BooleanVar(value=True)
    check_var_supplier = BooleanVar(value=True)

    checkbox_frame = Frame(preview_window)
    checkbox_frame.pack(pady=5)
    #สร้าง Checkbox สำหรับแต่ละหมวดหมู่ของรายงาน ให้ Checkbox นี้ควบคุมค่าของ check_var_stock
    Checkbutton(checkbox_frame, text="สินค้าในสต็อก", variable=check_var_stock).pack(side="left", padx=10)
    Checkbutton(checkbox_frame, text="สินค้าใกล้หมด", variable=check_var_low).pack(side="left", padx=10)
    Checkbutton(checkbox_frame, text="รายงานตามบริษัท", variable=check_var_supplier).pack(side="left", padx=10)

    save_button = Button(preview_window, text="บันทึกเป็น PDF", command=save_to_pdf, bg="green", fg="white")
    save_button.pack(pady=10)

    update_report(notebook)

# ฟังก์ชันอัปเดตรายงานเมื่อเลือกบริษัท
def update_report(notebook):#เรียกใช้ฟังก์ชัน update_report(notebook) ทันทีที่เปิดหน้าต่าง
    selected_supplier = supplier_var.get() #ดึงค่าบริษัทที่เลือกมา
    if selected_supplier == "ทั้งหมด":
        selected_supplier = None #ดึงข้อมูลทั้งหมด
    #ล้างข้อมูลเก่าออกจาก notebook
    for widget in notebook.winfo_children():
        widget.destroy() #ลบทุกแท็บก่อนโหลดข้อมูลใหม่

    products_in_stock, low_stock_products, supplier_summary, _ = fetch_data(selected_supplier)
    #สร้างตารางแสดงข้อมูล
    def create_treeview(parent, columns, data): # Frame 
        tree = ttk.Treeview(parent, columns=columns, show="headings")
        tree.pack(expand=True, fill="both")
        for col in columns:
            tree.heading(col, text=col, anchor="w") #การจัดวาง ชิดซ้าย
            tree.column(col, anchor="w", width=200) # ความกวาง
        for row in data: #แทรกข้อมูลเข้าไปใน Treeview
            tree.insert("", "end", values=row)
        return tree
    # สร้างแท็บ
    frame1 = ttk.Frame(notebook)
    notebook.add(frame1, text="📦 สินค้าในสต็อก")
    create_treeview(frame1, ("ID", "ชื่อสินค้า", "หมวดหมู่", "จำนวน", "บริษัท"), products_in_stock)

    frame2 = ttk.Frame(notebook)
    notebook.add(frame2, text="⚠️ สินค้าใกล้หมด")
    create_treeview(frame2, ("ID", "ชื่อสินค้า", "จำนวน", "บริษัท"), low_stock_products)

    frame3 = ttk.Frame(notebook)
    notebook.add(frame3, text="🏭 รายงานตามบริษัท")
    create_treeview(frame3, ("บริษัท", "หมวดหมู่", "รวมจำนวน"), supplier_summary)
    
# ฟังก์ชันบันทึก PDF
def save_to_pdf():
    file_path = asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF Files", "*.pdf")])#ตำแหน่งสำหรับบันทึกไฟล์ให้เลือกไฟล์ประเภท PDF เท่านั้น
    if not file_path:
        return  
    #ดึงค่าบริษัทที่ผู้ใช้เลือก
    selected_supplier = supplier_var.get()
    if selected_supplier == "ทั้งหมด":
        selected_supplier = None
    #ดึงข้อมูล สร้างเอกสาร กำหนด Font กำหนดตำแหน่ง
    products_in_stock, low_stock_products, supplier_summary, _ = fetch_data(selected_supplier)
    pdf = canvas.Canvas(file_path, pagesize=letter)
    pdf.setFont("ChulaNarak Regular", 12)
    y = 750

    # ฟังก์ชันวาดตารางสินค้าในสต็อก
    def draw_table_stock(data, headers, start_y): # วาดตาราง
        y = start_y
        x_start = 30
        col_widths = [50, 180, 100, 60, 120]  # กำหนดความกว้างของคอลัมน์
        #หัวตาราง
        pdf.setFont("ChulaNarak Regular", 14)
        pdf.drawString(220, y, "รายงานข้อมูลสินค้า - สินค้าที่มีในสต็อก")
        y -= 20

        pdf.drawString(30, y, "--------------------------------------------------------------------------------------------------------------------------------------")
        y -= 20
        
        def draw_header(headers, y_position):#รับ headersและพิมพ์ลงบนไฟล์ PDF
            x = x_start
            for idx, header in enumerate(headers):
                if idx < len(col_widths):
                    pdf.drawString(x, y_position, header)
                    x += col_widths[idx] #ขยับตำแหน่งไปคอลัมน์ถัดไป
            return y_position - 20

        y = draw_header(headers, y)

        for row in data:# เขียนค่าข้อมูลแต่ละแถวในตาราง
            x = x_start
            for idx, value in enumerate(row):
                pdf.drawString(x, y, str(value))
                x += col_widths[idx]
            y -= 20

        return y

    # ฟังก์ชันวาดตารางสินค้าใกล้หมด
    def draw_table_low(data, headers, start_y):
        y = start_y
        x_start = 30
        col_widths = [50, 200, 120, 140]

        pdf.setFont("ChulaNarak Regular", 14)
        pdf.drawString(220, y, "รายงานข้อมูลสินค้า - สินค้าใกล้หมดสต็อก")
        y -= 20
        pdf.drawString(30, y, "--------------------------------------------------------------------------------------------------------------------------------------")
        y -= 20
        
        def draw_header(headers, y_position):
            x = x_start
            for idx, header in enumerate(headers):
                if idx < len(col_widths):
                    pdf.drawString(x, y_position, header)
                    x += col_widths[idx]
            return y_position - 20

        y = draw_header(headers, y)

        for row in data:
            x = x_start
            for idx, value in enumerate(row):
                pdf.drawString(x, y, str(value))
                x += col_widths[idx]
            y -= 20

        return y

    # ฟังก์ชันวาดตารางรายงานตามบริษัท
    def draw_table_supplier(data, headers, start_y):
        y = start_y
        x_start = 30
        col_widths = [250, 150, 50]
        
        pdf.setFont("ChulaNarak Regular", 14)
        pdf.drawString(220, y, "รายงานข้อมูลสินค้า - รายการสินค้าตามบริษัท")
        y -= 20
        pdf.drawString(30, y, "--------------------------------------------------------------------------------------------------------------------------------------")
        y -= 20
        
        def draw_header(headers, y_position):
            x = x_start
            for idx, header in enumerate(headers):
                if idx < len(col_widths):
                    pdf.drawString(x, y_position, header)
                    x += col_widths[idx]
            return y_position - 20

        y = draw_header(headers, y)

        for row in data:
            x = x_start
            for idx, value in enumerate(row):
                pdf.drawString(x, y, str(value))
                x += col_widths[idx]
            y -= 20

        return y

    if check_var_stock.get(): #เช็ค ว่าผู้ใช้เลือกให้แสดง สินค้าในสต็อก หรือไม่ ถ้าใช่เรียก draw_table_stock() และส่งข้อมูล
        y = draw_table_stock(products_in_stock, ["ID", "ชื่อสินค้า", "หมวดหมู่", "จำนวน", "บริษัท"], y)

    if check_var_low.get():
        pdf.showPage()  # เพิ่มหน้าก่อนที่จะวาดตารางใหม่และ เซ็ตให้ y = 750 แล้วเริ่มเขียนข้อมูล
        y = 750
        y = draw_table_low(low_stock_products, ["ID", "ชื่อสินค้า", "จำนวน", "บริษัท"], y)

    if check_var_supplier.get():
        pdf.showPage()  # เพิ่มหน้าก่อนที่จะวาดตารางใหม่
        y = 750
        y = draw_table_supplier(supplier_summary, ["บริษัท", "หมวดหมู่","จำนวน"], y)

    # ปิดและบันทึกไฟล์ PDF และแจ้งเตือน
    pdf.save()
    tkinter.messagebox.showinfo("สำเร็จ", f"บันทึกไฟล์ PDF เรียบร้อยแล้ว: {file_path}")
    os.startfile(file_path)
        
##########################################################################

def loginwindow(root):
    #หน้าจอเข้าสู่ระบบ
    logroot = Toplevel(root)
    logroot.title("เข้าสู่ระบบ")
    logroot.geometry("1239x650+0+0")
    logroot.configure(bg="#EBF8FE")
    
    OUTPUT_PATH = Path(__file__).parent
    ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\chanan\Pictures\Img\login\build\assets\frame0")
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    canvas = Canvas(logroot,bg = "#EBF8FE",height = 650,width = 1239,bd = 0,highlightthickness = 0,relief = "ridge")
    canvas.place(x = 0, y = 0)

    image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
    image_1 = canvas.create_image(630.0,324.0,image=image_image_1)

    image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
    image_2 = canvas.create_image(600.0,328.0,image=image_image_2)

    def set_placeholder(entry, placeholder_text, is_password=False):
        def on_focus_in(event):
            if entry.get() == placeholder_text:
                entry.delete(0, "end")
                if is_password:
                    entry.config(show="*")  # เปิดการซ่อนรหัสผ่านเมื่อพิมพ์

        def on_focus_out(event):
            if entry.get() == "":
                entry.insert(0, placeholder_text)
                if is_password:
                    entry.config(show="")  # แสดง placeholder ธรรมดา

        # ตั้งค่าเริ่มต้น
        entry.insert(0, placeholder_text)
        entry.config(fg="black")
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # Entry สำหรับชื่อผู้ใช้
    username_entry = Entry(logroot, foreground="#5C7FCB",font=("Inter SemiBold", 24), bd=0, highlightthickness=0,bg="#8FB1E0")
    username_entry.place(x=350, y=224)
    set_placeholder(username_entry, "ชื่อผู้ใช้")

    # Entry สำหรับรหัสผ่าน
    password_entry = Entry(logroot, foreground="#5C7FCB",font=("Inter SemiBold", 24), bd=0, highlightthickness=0,bg="#8FB1E0")
    password_entry.place(x=350, y=314)
    set_placeholder(password_entry, "รหัสผ่าน", is_password=True)

    def pick_date(entry):
        def grab_date():
            entry.delete(0, END)
            entry.insert(0, cal.get_date())
            date_window.destroy()

        # สร้างหน้าต่างสำหรับเลือกวันที่
        date_window = Toplevel(register_window)
        date_window.grab_set()
        date_window.title("เลือกวันที่")
        date_window.geometry("343x337+590+370")
        cal = Calendar(date_window, selectmode="day", date_pattern="dd/mm/yyyy")
        cal.pack(pady=10)
        submit_btn = Button(date_window, text="เลือก", command=grab_date)
        submit_btn.pack()

    # ฟังก์ชันสำหรับเปิดหน้าต่างสมัครสมาชิก
    def open_register_window():
        global register_window
        OUTPUT_PATH = Path(__file__).parent
        ASSETS_PATH = OUTPUT_PATH / Path(r"C:\build\assets\frame0")

        def relative_to_assets(path: str) -> Path:
            return ASSETS_PATH / Path(path)  
        # สร้างหน้าต่างสำหรับการสมัครสมาชิก
        register_window = Toplevel(logroot)
        register_window.title("สมัครสมาชิก")
        register_window.geometry("1239x650+0+0")
        register_window.configure(bg="#EBF8FE")
        register_window.transient(logroot)
        canvas = Canvas(register_window,bg = "#EBF8FE",height = 650,width = 1239,bd = 0,highlightthickness = 0,relief = "ridge")
        canvas.place(x = 0, y = 0)
        
        style = ttk.Style()
        style.theme_use("alt")
        style.configure("TCombobox",
            fieldbackground="#8FB1E0",  # สีพื้นหลังในช่องป้อนข้อความ
            background="#8FB1E0",       # สีพื้นหลังตัวเลือก
            foreground="#000000",       # สีตัวอักษร
            borderwidth=0,              # กำหนด border เป็น 0
            highlightthickness=0,        # กำหนดขอบไฮไลต์ให้บางที่สุด
            arrowcolor="#FFED23",font=("Inter SemiBold", 18)
        )
        
        image_image_1 = PhotoImage(file=relative_to_assets("image_1.png"))
        image_1 = canvas.create_image(693.0,350.0,image=image_image_1)

        image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
        image_2 = canvas.create_image(622.0,324.0,image=image_image_2)

        button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
        button_1 = Button(register_window,image=button_image_1,borderwidth=0,highlightthickness=0,command=register_window.destroy,relief="flat")
        button_1.place(x=665.0,y=560.0,width=142.0,height=43.0)

        image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
        image_3 = canvas.create_image(149.0,94.0,image=image_image_3)

        canvas.create_text(448.0,42.0,anchor="nw",text="สมัครสมาชิก",fill="#FFFFFF",font=("InriaSans Bold", 64 * -1))
        canvas.create_rectangle(73.0,225.0,454,227,fill="#000000",outline="")
        canvas.create_rectangle(72.0,326.0,453,328,fill="#000000",outline="")
        canvas.create_rectangle(71.0,422.0,452,424,fill="#000000",outline="")
        canvas.create_rectangle(485.0,226,867.0,228,fill="#000000",outline="")
        canvas.create_rectangle(492,324,874,327,fill="#000000",outline="")
        canvas.create_rectangle(492,421,874.,424,fill="#000000",outline="")
        canvas.create_rectangle(490.0,511,871,514,fill="#000000",outline="")
        canvas.create_rectangle(71.0,510.0,452,512,fill="#000000",outline="")
        
        image_image_4 = PhotoImage(file=relative_to_assets("image_4.png"))
        image_4 = canvas.create_image(853,295,image=image_image_4)

        image_image_5 = PhotoImage(file=relative_to_assets("image_5.png"))
        image_5 = canvas.create_image(434.0,197.0,image=image_image_5)

        image_image_6 = PhotoImage(file=relative_to_assets("image_6.png"))
        image_6 = canvas.create_image(434.0,301.0,image=image_image_6)

        image_image_7 = PhotoImage(file=relative_to_assets("image_7.png"))
        image_7 = canvas.create_image(430.0,491.0,image=image_image_7)

        image_image_8 = PhotoImage(file=relative_to_assets("image_8.png"))
        image_8 = canvas.create_image(434.0,388.0,image=image_image_8)

        image_image_9 = PhotoImage(file=relative_to_assets("image_9.png"))
        image_9 = canvas.create_image(846.0,198.0,image=image_image_9)

        image_image_10 = PhotoImage(file=relative_to_assets("image_10.png"))
        image_10 = canvas.create_image(848.0,393.0,image=image_image_10)
        
        # สร้าง Entry สำหรับกรอกข้อมูล
        username_entry1 = Entry(register_window, foreground="#5C7FCB",font=("Inter SemiBold", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        username_entry1.place(x=75, y=190)
        set_placeholder(username_entry1, "ชื่อผู้ใช้")
        username_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        username_error_label.place(x=75, y=230)

        password_entry = Entry(register_window, foreground="#5C7FCB",font=("Inter SemiBold", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        password_entry.place(x=75, y=290)
        set_placeholder(password_entry, "รหัสผ่าน", is_password=True)
        password_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        password_error_label.place(x=75, y=330)

        email_entry = Entry(register_window, font=("Arial", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        email_entry.place(x=490, y=190)
        set_placeholder(email_entry, "อีเมล")
        email_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        email_error_label.place(x=490, y=230)

        birthday_entry = Entry(register_window, font=("Arial", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        birthday_entry.place(x=490, y=385)
        birthday_error_label= Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        birthday_error_label.place(x=490, y=430)
        set_placeholder(birthday_entry, "วันเกิด (dd/mm/yyyy)")
        birthday_entry.bind("<1>", lambda event: pick_date(birthday_entry))
        
        cardnumber_entry = Entry(register_window, font=("Arial", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        cardnumber_entry.place(x=75, y=385)
        set_placeholder(cardnumber_entry, "เลขบัตรประชาชน")
        cardnumber_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        cardnumber_error_label.place(x=75, y=430)
        
        address_entry = Entry(register_window, font=("Arial", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        address_entry.place(x=490, y=285)
        set_placeholder(address_entry, "ที่อยู่")
        address_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        address_error_label.place(x=490, y=330)

        phone_entry = Entry(register_window, font=("Arial", 20), bd=0, highlightthickness=0,bg="#8FB1E0")
        phone_entry.place(x=75, y=473)
        set_placeholder(phone_entry, "เบอร์โทรศัพท์")
        phone_error_label = Label(register_window, text="", fg="red",bg="#8FB1E0")  # ข้อความข้อผิดพลาด
        phone_error_label.place(x=75, y=530)
        
        role_entry = Label(register_window,text="ตำแหน่ง", font=("Arial", 20),bg="#8FB1E0")
        role_entry.place(x=496, y=470)
        style.configure("TCombobox",fieldbackground="#8FB1E0",bd=0, highlightthickness=0,arrowcolor="#FFED23" )
        entry_roles = ttk.Combobox(
            register_window,
            values=["เจ้าของร้าน","เจ้าหน้าที่สต๊อกสินค้า","เภสัชกร","ผู้ช่วยเภสัชกร(พนักงาน)"],
            foreground="#000000",
            font=("Inter SemiBold", 20),  # ตั้งขนาดฟอนต์
            height=7,
            width=17,           # กำหนดความกว้าง          
            state="normal"      # อนุญาตให้พิมพ์ได้ 
        )
        entry_roles.place(x=596, y=473)
        
        def setPreviewPic(filepath):
            global img
            img = Image.open(filepath)
            img = img.resize((263, 366), Image.Resampling.LANCZOS)
            img = ImageTk.PhotoImage(img)
            show_pic.config(image=img)
            pathEntry.delete(0, END)
            pathEntry.insert(0, filepath)

        def selectPic():
            register_window.grab_set()
            global filename
            filename = filedialog.askopenfilename(
                initialdir=os.getcwd(),
                title="Select Image",
                filetypes=(("PNG Images", "*.png"), ("JPEG Images", "*.jpg;*.jpeg"))
            )
            if filename:
                setPreviewPic(filename)
            register_window.grab_release() 

        def register_user(image_path):
            username = username_entry1.get()
            password = password_entry.get()
            email = email_entry.get()
            birthday = birthday_entry.get()
            cardnumber = cardnumber_entry.get()
            address = address_entry.get()
            phone = phone_entry.get()
            role = entry_roles.get()

            username_error_label.config(text="")
            password_error_label.config(text="")
            email_error_label.config(text="")
            cardnumber_error_label.config(text="")
            address_error_label.config(text="")
            phone_error_label.config(text="")
            birthday_error_label.config(text="")
            
            # ตัวแปรสำหรับการตรวจสอบข้อผิดพลาด
            has_error = False

            # ตรวจสอบข้อมูลว่าครบทุกช่องหรือไม่
            if not (username and password and email and birthday and cardnumber and address and phone):
                tkinter.messagebox.showerror("ข้อผิดพลาด", "กรุณากรอกข้อมูลให้ครบทุกช่อง")
                return

            email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
            if not re.match(email_pattern, email):
                email_error_label.config(text="กรุณากรอกอีเมลให้ถูกต้อง (เช่น example@email.com)")
                has_error = True
        
            if not birthday:
                birthday_error_label.config(text="กรุณากรอกวันเกิด")
                has_error = True

            # ตรวจสอบความยาวของชื่อผู้ใช้
            if len(username) < 8:
                username_error_label.config(text="ชื่อผู้ใช้ต้องมีอย่างน้อย 8 ตัวอักษร")
                has_error = True
            
            if not any(char.isupper() for char in username):
                username_error_label.config(text="ชื่อผู้ใช้ต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว")
                has_error = True

            # ตรวจสอบรหัสผ่าน
            if len(password) < 8:
                password_error_label.config(text="รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")
                has_error = True
            
            if not any(char.isdigit() for char in password):
                password_error_label.config(text="รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
                has_error = True

            if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
                password_error_label.config(text="รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&*)")
                has_error = True

            # ตรวจสอบเลขบัตรประชาชน
            if not cardnumber.isdigit() or len(cardnumber) != 13:
                cardnumber_error_label.config(text="เลขบัตรประชาชนต้องเป็นตัวเลข 13 หลัก")
                has_error = True

            # ตรวจสอบเบอร์โทรศัพท์
            if not phone.isdigit() or len(phone) != 10:
                phone_error_label.config(text="เบอร์โทรศัพท์ต้องเป็นตัวเลข 10 หลัก")
                has_error = True
                
            if role == "เจ้าของร้าน":
                s.execute("SELECT COUNT(*) FROM users WHERE role = ?", ("เจ้าของร้าน",))
                result = s.fetchone()
                if result[0] > 0:
                    tkinter.messagebox.showerror("ข้อผิดพลาด", "มีเจ้าของร้านอยู่แล้ว ไม่สามารถสมัครได้")
                    return
            
            if has_error:
                return
            
            if not has_error:
                try:
                    savePic(filename)
                except Exception as e:
                    tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}")
            
            if username_error_label.cget("text") == "" and password_error_label.cget("text") == "" and email_error_label.cget("text") == "" and cardnumber_error_label.cget("text") == "" and address_error_label.cget("text") == "" and phone_error_label.cget("text") == "" and birthday_error_label.cget("text") == "":
                try:
                    # เพิ่มข้อมูลลงในฐานข้อมูล
                    s.execute("INSERT INTO users (username, password, email, birthday, cardnumber, address, phone, image_path,role) VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)",
                    (username, password, email, birthday, cardnumber, address, phone, image_path,role))

                    # บันทึกการเปลี่ยนแปลง
                    logins.commit()
                    tkinter.messagebox.showinfo("สำเร็จ", "สมัครสมาชิกเรียบร้อยแล้ว")

                    # ปิดหน้าต่างสมัครสมาชิก
                    register_window.destroy()

                except sqlite3.IntegrityError as e:
                    if "users.email" in str(e):
                        email_error_label.config(text="อีเมลนี้ถูกใช้ไปแล้ว")
                    elif "users.username" in str(e):
                        username_error_label.config(text="ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว")
                    elif "users.phone" in str(e):
                        phone_error_label.config(text="เบอร์โทรศัพท์นี้ถูกใช้ไปแล้ว")
                    elif "users.cardnumber" in str(e):
                        cardnumber_error_label.config(text="เลขบัตรประชาชนนี้ถูกใช้ไปแล้ว")
                    else:
                        tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")
        
        def savePic(filename):
            if not filename:
                tkinter.messagebox.showwarning("คำเตือน", "ไม่มีไฟล์ที่เลือก")
                return
            save_directory = r"C:\Users\chanan\Pictures\Img"
            new_file_path = os.path.join(save_directory, os.path.basename(filename))
            try:
                shutil.copy(filename, new_file_path)
            except Exception as e:
                tkinter.messagebox.showerror("คำเตือน", f"ไม่สามารถอัปโหลดรุ)ได้: {e}")
                
        # สร้าง Frame สำหรับการเลือกไฟล์
        frame_img = Frame(register_window, bg="#8FB1E0")
        frame_img.place(x=882, y=558)  # กำหนดตำแหน่งใหม่สำหรับกรอบเลือกไฟล์

        # สร้างปุ่มเพื่อเลือกไฟล์
        selectBtn = customtkinter.CTkButton(frame_img, text="อัปโหลดไฟล์", width=50, command=selectPic)
        selectBtn.grid(row=0, column=0, padx=10, pady=5, ipady=0, sticky="e")

        # สร้างช่องแสดง path ของไฟล์
        pathEntry = customtkinter.CTkEntry(frame_img, width=200)
        pathEntry.grid(row=0, column=1, padx=10, pady=5, ipady=0, sticky="e")

        show_pic = Label(register_window, bg="#8FB1E0")
        show_pic.place(x=912, y=169)

        # ให้แสดงภาพตัวอย่างที่กำหนด
        setPreviewPic(r"C:\Users\chanan\Pictures\Img\login\build\assets\frame0\image_1.png")
            
        button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
        button_2 = Button(register_window,image=button_image_2,borderwidth=0,highlightthickness=0,command=lambda:[register_user(filename)],relief="flat")
        button_2.place(x=260.0, y=535.0,width=399.0,height=78.0)
        register_window.mainloop()

##########################################################################

    # ฟังก์ชันเข้าสู่ระบบ
    def login_user():
        try:
            username = username_entry.get()
            password = password_entry.get()
            if not username or not password:
                tkinter.messagebox.showwarning("ข้อผิดพลาด", "กรุณากรอกชื่อผู้ใช้และรหัสผ่าน")
                return
        except Exception as e:
            tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")

        try:
            s.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
            user = s.fetchone()
            if user:
                global current_user
                current_user = user  # เก็บข้อมูลผู้ใช้ในตัวแปร global
                tkinter.messagebox.showinfo("สำเร็จ", "เข้าสู่ระบบสำเร็จ")
                logroot.destroy()
                main_window(root)
                
            else:
                tkinter.messagebox.showwarning("ข้อผิดพลาด", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
        except sqlite3.Error as e:
            tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

##########################################################################

    # การเปลี่ยนรหัส
    def open_forgot_password_window():
        OUTPUT_PATH = Path(__file__).parent
        ASSETS_PATH = OUTPUT_PATH / Path(r"C:\Users\chanan\Documents\build\assets\frame0") #สร้างหน้าต่าง GUI
        def relative_to_assets(path: str) -> Path:
            return ASSETS_PATH / Path(path)
        
        forgot_window = Toplevel(logroot)
        forgot_window.title("ลืมรหัสผ่าน")
        forgot_window.geometry("1239x650+0+0")
        forgot_window.config(bg="#EBF8FE")
        
        canvas = Canvas(forgot_window,bg = "#EBF8FE",height = 650, width = 1239,  bd = 0,highlightthickness = 0,relief = "ridge")

        canvas.place(x = 0, y = 0)

        def set_placeholder(entry, placeholder_text, is_password=False): # รับพารามิเตอร์ 3
            def on_focus_in(event): # เมื่อคลิกเข้าไปในช่องกรอก ตัวหนังสือก็จะหายไป
                if entry.get() == placeholder_text:  #เช็คข้อมูลว่า เป็นplaceholder_textมั้ย
                    entry.delete(0, "end") 
                    if is_password:
                        entry.config(show="*")  # เปิดการซ่อนรหัสผ่านเมื่อพิมพ์

            def on_focus_out(event): #ผู้ใช้คลิกออกจากช่องกรอก
                if entry.get() == "": #ช่องกรอกข้อมูลว่างเปล่า
                    entry.insert(0, placeholder_text) #จะใส่ข้อความ placeholder กลับเข้าไปในช่อง
                    if is_password:
                        entry.config(show="")  # แสดง placeholder ธรรมดา

            # ตั้งค่าเริ่มต้น คำว่าอีเมล
            entry.insert(0, placeholder_text)
            entry.config(fg="black")
            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out) #เรียกฟังก์ชัน

        # ช่องกรอกอีเมล
        forgot_email_entry = Entry(forgot_window, font=("Arial", 20), bd=0, highlightthickness=0, bg="#8FB1E0", fg='black')
        forgot_email_entry.place(x=402, y=230)
        set_placeholder(forgot_email_entry, "อีเมล") # ตั้ง placeholder สำหรับช่องกรอกอีเมล

        def  reset_password():   
            email = forgot_email_entry.get() #กดยืนยัน
            try:
                s.execute("SELECT * FROM users WHERE email = ?", (email,)) #ค้นหา
                user = s.fetchone()
                if not user:
                    tkinter.messagebox.showwarning("ข้อผิดพลาด", "ไม่พบอีเมลในระบบ")
                    forgot_email_entry.delete(0, "end")
                    return
                else:
                    # ในการสร้างช่องกรอกรหัสผ่านใหม่
                    new_password_entry = Entry(forgot_window, font=("Arial", 20), bd=0, highlightthickness=0, bg="#8FB1E0", fg='black')
                    new_password_entry.place(x=171, y=445)
                    set_placeholder(new_password_entry, "รหัสผ่านใหม่", is_password=True)

                    confirm_password_entry = Entry(forgot_window, font=("Arial", 20), bd=0, highlightthickness=0, bg="#8FB1E0", fg='black')
                    confirm_password_entry.place(x=642, y=445)
                    set_placeholder(confirm_password_entry, "ยืนยันรหัสผ่านใหม่", is_password=True)
                            
                    def confirm_reset(): 
                        new_password = new_password_entry.get()
                        confirm_password = confirm_password_entry.get() #กดปุ่มยืนยัน ลงมาตรวจสอบรหัสว่าตรงตามเงื่อนไขมั้ย

                        if not new_password or not confirm_password:# ช่องกรอกว่าง
                            tkinter.messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน")
                            return

                        if len(new_password) < 8:
                            tkinter.messagebox.showwarning("คำเตือน", "รหัสผ่านต้องมีความยาวอย่างน้อย 8 ตัวอักษร")
                            return

                        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", new_password):
                            tkinter.messagebox.showwarning("คำเตือน", "รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (!@#$%^&*)")
                            return

                        if not any(char.isdigit() for char in new_password):
                            tkinter.messagebox.showwarning("คำเตือน", "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
                            return

                        if new_password != confirm_password:
                            tkinter.messagebox.showwarning("คำเตือน", "รหัสผ่านไม่ตรงกัน")
                            return

                        try: # รหัสผ่านใหม่จะถูกอัพเดตในฐานข้อมูล และแสดงข้อความสำเร็จ
                            s.execute("UPDATE users SET password = ? WHERE email = ?", (new_password, email))
                            logins.commit()
                            tkinter.messagebox.showinfo("สำเร็จ", "เปลี่ยนรหัสผ่านเรียบร้อยแล้ว!")
                            forgot_window.destroy()
                            
                        except sqlite3.Error as e:
                            tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")

                    canvas.create_rectangle( 168.0,484,602,486,fill="#000000",outline="")
                    # เส้นสีดำตบแต่ง
                    canvas.create_rectangle( 639.0,484.505126953125,1073.9999907611,486.9999389366817,fill="#000000",outline="")
                        
                    canvas.create_text(516.0,382.0, anchor="nw",text="เปลี่ยนรหัสผ่านใหม่",fill="#000000",font=("Inder Regular", 30 * -1))
                    # ฟังก์ชันยืนยันการเปลี่ยนรหัสผ่าน
                    Button(forgot_window, text="ยืนยัน", bg="#5C7FCB", fg="white",font=("Arial", 32), command=confirm_reset).place(x=441,y=523,width=380, height=55)
            except sqlite3.Error as e:
                tkinter.messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {e}")
        # รูปปุ่มลืมรหัส
        buttonsubmit = PhotoImage( file=relative_to_assets("button_2.png"))
        button_2 = Button( forgot_window,image=buttonsubmit,borderwidth=0,highlightthickness=0,command=reset_password,relief="flat")
        button_2.place(x=463.0,y=283.0, width=303.51568603515625,height=78.0)
        
        try: #เรียกภาพขึ้นมาและสร้างที่อยู่
            image_image_1 = PhotoImage( file=relative_to_assets("image_1.png"))
            image_1 = canvas.create_image( 650.0,324.0,image=image_image_1)

            image_image_2 = PhotoImage(file=relative_to_assets("image_2.png"))
            image_2 = canvas.create_image(618.0,328.0,image=image_image_2)

            image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
            image_3 = canvas.create_image(235.23072814941406,111.0,image=image_image_3)
        except Exception as e:
            tkinter.messagebox.showerror("ข้อผิดพลาดในการโหลดภาพ", f"ไม่สามารถโหลดภาพ: {e}")
            return

        canvas.create_text( 506.0,63.0,anchor="nw",text="ลืมรหัส",fill="#FFFFFF",font=("InriaSans Bold", 64 * -1))
    # เส้นสีดำตบแต่ง
        canvas.create_rectangle(400.0,268.0,834,270,fill="#000000",outline="")
        
        canvas.create_text(487.0,175.0,anchor="nw",text="กรอกอีเมลที่ลงทะเบียนไว้",fill="#000000",font=("Inder Regular", 30 * -1))

        image_image_6 = PhotoImage(file=relative_to_assets("image_6.png"))
        image_6 = canvas.create_image(812.0,251.0,image=image_image_6)
        forgot_window.mainloop()

#######################################################

    #ปุ่มเข้าสู่ระบบ
    button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
    button_1 = Button(logroot,image=button_image_1, borderwidth=0,highlightthickness=0,command=open_register_window,relief="flat")
    button_1.place(x=440.0, y=518.0, width=142.0, height=43.0)

    button_image_2 = PhotoImage(file=relative_to_assets("button_2.png"))
    button_2 = Button(logroot,image=button_image_2,borderwidth=0,highlightthickness=0,command=open_forgot_password_window,relief="flat")
    button_2.place(x=635.0,y=516.0,width=106.0,height=43.0)

    image_image_3 = PhotoImage(file=relative_to_assets("image_3.png"))
    image_3 = canvas.create_image(330.0,125.0,image=image_image_3)

    canvas.create_text(500.0,77.0,anchor="nw",text="เข้าสู่ระบบ",fill="#FFFFFF",font=("InriaSans Bold", 64 * -1))

    canvas.create_rectangle(350.0,270.0,850.0,272.0,fill="#000000",outline="")

    canvas.create_rectangle(350.0,360.0,850.0,362.49481198355676,fill="#000000",outline="")

    button_image_3 = PhotoImage(file=relative_to_assets("button_3.png"))
    button_3 = Button(logroot,image=button_image_3,borderwidth=0,highlightthickness=0, command=login_user,relief="flat")
    button_3.place(x=400.0,y=421.0,width=399.0,height=78.0)

    image_image_4 = PhotoImage(file=relative_to_assets("image_4.png"))
    image_4 = canvas.create_image(840.0,250.0,image=image_image_4)

    image_image_5 = PhotoImage(file=relative_to_assets("image_5.png"))
    image_5 = canvas.create_image(840.0,343.0,image=image_image_5)
    logroot.mainloop()

##########################################################################

if __name__ == "__main__":
    root = Tk()
    root.geometry("1259x800+0+0")
    root.configure(bg = "#EBF8FE")
    root.withdraw()  # ซ่อนหน้าต่างหลักชั่วคราว
    show_root = None
    add_root = None
    update_root = None
    employees_root = None
    maker_root = None
    remove_root = None
    loginwindow(root)  # แสดงหน้าต่างล็อกอิน
    root.mainloop()  # เริ่มโปรแกรมหลัก