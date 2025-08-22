"""
Functions need to be refine
- frame4
- read the values
- re-arrange the 
"""

# import area ---------------------------------------------------------------------------
import customtkinter as ctk
import tkinter.ttk as ttk  # Add this to your imports at the top if not already
from tkinter import filedialog  # Make sure this is at the top of your script
import tkinter.messagebox as messagebox

from redfish import redfish_client
import urllib3

import json
import os
import tkinter as tk
import random

#create window > frames > labels/entries/button > buttons' functions

# import area END ---------------------------------------------------------------------------


# define area ---------------------------------------------------------------------------
global bmc_ip, bmc_user, bmc_pw, os_ip, os_user, os_pw
global file_paths
global outer_edge, inner_edge
global entry_width
global sd_block, registry_block
outer_edge=15
inner_edge=5
entry_width=450

sd_block = {}
registry_block = {}

# define area END ---------------------------------------------------------------------------


# function area ---------------------------------------------------------------------------
class MyFrame(ctk.CTkFrame): # defining a custom class called MyFrame, inherits from ctk.CTkFrame
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # # add widgets onto the frame, for example:
        # self.label = ctk.CTkLabel(self)
        # self.label.grid(row=0, column=0, padx=20)

class CredentialApp(ctk.CTk):

    # GUI area ---------------------------------------------------------------------------
    def print_separate(self): #for separate purpose
        sep = "=="*30
        self.log_box.insert("end", sep+"\n\n")
        print(sep+"\n\n")
        self.log_box.see("end") #It scrolls the CTkTextbox to the bottom, ensuring the latest message is visible 

    def center_the_window(self): #for centered window, nut mostly not really accurate
        self.update_idletasks()  # Let widgets define window size first

        # Get actual size after layout
        window_width = self.winfo_width()
        window_height = self.winfo_height()
        # print(window_width, window_height)

        # Get screen dimensions
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        # print(screen_width, screen_height)

        # Calculate x and y coordinates for the center
        x = int((screen_width / 2) - (window_width / 2))
        y = int((screen_height / 2) - (window_height / 2))

        # self.geometry("500x500") # WINDOW SIZE
        # self.resizable(False, False) # WINDOW SIZE FIXED or RESIZE

        self.geometry(f"{window_width}x{window_height}+{x}+{y}") # Set the geometry to center the window

    # GUI area END ---------------------------------------------------------------------------


    # redfish area ---------------------------------------------------------------------------

    def compare(self): # finally shei duck compare la meh?

        # Get file paths from the entry boxes
        original_path = self.file_paths["bios_sd_original.txt"].get() 
        edited_path = self.file_paths["bios_sd_edited.txt"].get()

        if not os.path.exists(original_path) or not os.path.exists(edited_path):
            self.log_box.insert("end", "❌ One or both file paths are invalid or missing.\n")
            print("❌ One or both file paths are invalid or missing.")
            self.print_separate()
            return

        # Compare and generate diff file
        self.compare_and_dump_changes(original_path, edited_path)

    def parse_bios_file(self, filepath):
        parsed = {}
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if ":" in line:
                    key, val = line.strip().split(":", 1)
                    parsed[key.strip()] = val.strip()
        return parsed
    
    def compare_and_dump_changes(self, original_path, edited_path, output_path="changed_bios_attributes.txt"):
        original = self.parse_bios_file(original_path)
        edited = self.parse_bios_file(edited_path)

        changes = []
        for key in original:
            if key in edited and original[key] != edited[key]:
                changes.append((key, original[key], edited[key]))

        if changes:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("==== Changed BIOS Attributes ====\n\n")
                for key, orig_val, edit_val in changes:
                    f.write(f"Attribute: {key}\n")
                    f.write(f"Original : {orig_val}\n")
                    f.write(f"Edited   : {edit_val}\n\n")

            # set compare_path_entry --> created comparison txt file path
            self.compare_result_entry.delete(0, "end")
            self.compare_result_entry.insert(0,os.path.abspath(output_path))

            self.log_box.insert("end", f"[✔] Changes saved to {os.path.abspath(output_path)}\n")
            print(f"[✔] Changes saved to {os.path.abspath(output_path)}")
        else:
            self.log_box.insert("end", "[✔] No changes found.\n")
            print("[✔] No changes found.")

        self.print_separate()


    def patch(self): # shau pei la!!! mo file goi tiu mo ar?! yau file sin lai goi la poor guy
        global registry_block
        changes_file = self.compare_result_entry.get()
        bios_settings_uri = "/redfish/v1/Systems/Self/Bios/SD"

        if not os.path.exists(changes_file):
            self.log_box.insert("end", f"❌ File not found: {changes_file}. File not exists or entry box is not filled. Pls re-confirm.\n")
            print(f"❌ File not found: {changes_file}. File not exists or entry box is not filled. Pls re-confirm.")
            self.print_separate()
            return

        # Step 1: Reuse BMC creds
        bmc_ip = self.entries["BMC IP"].get()
        bmc_user = self.entries["BMC Username"].get()
        bmc_pw = self.entries["BMC Password"].get()

        # Step 2: Login
        try:
            client = redfish_client(base_url="https://" + bmc_ip, username=bmc_user, password=bmc_pw)
            client.login()
        except Exception as e:
            self.log_box.insert("end", f"❌ Login failed: {e}\n")
            print(f"❌ Login failed: {e}")
            return

        # Step 3: Parse file
        attributes = {}
        current_attr = None
        with open(changes_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("Attribute:"):
                    current_attr = line.split(":", 1)[1].strip()
                elif line.startswith("Edited") and current_attr:
                    edited_val = line.split(":", 1)[1].strip()

                    # Convert string to bool/int/str
                    if edited_val.lower() == "true":
                        attributes[current_attr] = True
                    elif edited_val.lower() == "false":
                        attributes[current_attr] = False
                    elif edited_val.isdigit():
                        attributes[current_attr] = int(edited_val)
                    else:
                        attributes[current_attr] = edited_val
                    current_attr = None
        print(attributes)
        if not attributes:
            self.log_box.insert("end", "❌ No changes found to patch.\n")
            return

        # Step 4: Get ETag


        etag_resp = client.get(bios_settings_uri)
        if etag_resp.status != 200:
            self.log_box.insert("end", f"❌ Failed to fetch BIOS settings. Status code: {etag_resp.status}\n")
            return
        print(etag_resp.getheaders())  # Show all headers returned
        current_bios_attributes = etag_resp.dict.get("Attributes", {})

        etag = etag_resp.getheader("ETag") or etag_resp.dict.get("@odata.etag")
        if not etag:
            self.log_box.insert("end", "❌ Failed to retrieve ETag.\n")
            return

        # Step 5: Send PATCH
        # Validate all attribute keys exist in registry_block

        # Before patching
        valid_attributes = {k: v for k, v in attributes.items() if k in current_bios_attributes}

        if not valid_attributes:
            self.log_box.insert("end", "⚠️ No valid attributes to patch after validation.\n")
            print("⚠️ No valid attributes to patch after validation.")
            return

        patch_body = {"Attributes": valid_attributes}
        headers = {
            "Content-Type": "application/json",
            "If-Match": etag
        }

        try:
            response = client.patch(bios_settings_uri, body=patch_body, headers=headers)
            if response.status in [200, 202, 204]:
                self.log_box.insert("end", "[✔] BIOS settings patched successfully. Will apply on next boot.\n")
            else:
                self.log_box.insert("end", f"❌ PATCH failed. Status: {response.status}\n{response.text}\n")
        except Exception as e:
            self.log_box.insert("end", f"❌ Error during patch: {e}\n")

        pending_response = client.get("/redfish/v1/Systems/Self/Bios/Pending")
        print("Pending Attributes:", pending_response.dict.get("Attributes", {}))

        print("Sending PATCH:", json.dumps(patch_body, indent=4))
        print("With headers:", headers)       
        print("[📤] PATCH Body:\n", json.dumps(patch_body, indent=4))
        print("[📬] PATCH Status:", response.status)
        print("[📬] PATCH Text:", response.text)
   
        self.print_separate()

    def revise(self):
        """
        Reads Treeview rows, extracts updated values, and overwrites bios_sd_edited.txt.
        """
        revised_data = []

        for row_id in self.tree.get_children():
            values = self.tree.item(row_id, "values")
            if len(values) < 4:
                continue
            attr_name, _, _, revised_value = values
            real_val = self.display_to_real_map.get(attr_name, {}).get(revised_value, revised_value)
            revised_data.append((attr_name, real_val))

        if not revised_data:
            self.log_box.insert("end", "⚠️ No data to write.\n")
            return

        print(revised_data)

        # Write back to bios_sd_edited.txt
        output_path = "bios_sd_edited.txt"

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("==== BIOS Settings Dump ====\n\n")
                for attr, val in revised_data:
                    f.write(f"{attr}: {val}\n")

            self.log_box.insert("end", f"[✔] bios_sd_edited.txt updated with revised values.\n")
            print(f"[✔] bios_sd_edited.txt updated with revised values.")
            self.log_box.see("end")
        except Exception as e:
            self.log_box.insert("end", f"❌ Failed to write to bios_sd_edited.txt: {e}\n")
            print(f"❌ Failed to write to bios_sd_edited.txt: {e}")


    def perform_redfish_dump(self, ip, user, pw): # ok la , ha min 3 gor dou gwan si dick, find_bios/dump_bios/etc
        # Step 1: Login
        try:
            client = redfish_client(base_url='https://' + ip, username=user, password=pw)
            client.login()
        except Exception as e:
            self.log_box.insert("end", f"❌ Failed to connect to Redfish: {e}\n\n")
            print(f"❌ Failed to connect to Redfish: {e}")
            return

        # Step 2: Find registry path
        bios_attribute_registry = self.find_bios_attribute_registry(client)
        if not bios_attribute_registry:
            self.log_box.insert("end", "❌ BIOS Attribute Registry not found.\n\n")
            print("❌ BIOS Attribute Registry not found.")
            return

        # self.log_box.insert("end", f"📁 BIOS registry path: {bios_attribute_registry}\n") # your are looking for a useless comment hehe =b

        # Step 3: Save raw JSON
        system = client.get(bios_attribute_registry)
        with open("bios_registry_raw.json.txt", "w", encoding="utf-8") as f:
            f.write(json.dumps(system.dict, indent=4))
        self.log_box.insert("end", "[✔] BIOS raw registry saved to bios_registry_raw.json.txt\n")
        print("[✔] BIOS raw registry saved to bios_registry_raw.json.txt")

        # Step 4: Dump human-readable registry
        self.dump_bios_registry_txt(client, bios_attribute_registry)
        self.log_box.insert("end", "[✔] BIOS attribute registry dumped.\n")
        print("[✔] BIOS attribute registry dumped.")

        # [✔] Dump BIOS SD settings (to original + edited .txt)
        self.dump_bios_settings_txt(client)
        self.print_separate()

# Then continue saving files, etc...


    # get the json file name :/redfish/v1/Registries/BiosAttributeRegistryCapa0.en-US.0.70.0.json
    def find_bios_attribute_registry(self, client):
        """
        Automatically finds the BIOS Attribute Registry JSON URI by traversing /redfish/v1/Registries.
        """
        registries_resp = client.get("/redfish/v1/Registries")
        if registries_resp.status != 200:
            print("Failed to access /redfish/v1/Registries")
            return None

        registries = registries_resp.dict.get("Members", [])
        
        for reg in registries:
            reg_uri = reg.get("@odata.id")
            if not reg_uri:
                continue

            # Step into each registry
            sub_reg_resp = client.get(reg_uri)
            if sub_reg_resp.status != 200:
                continue

            location_array = sub_reg_resp.dict.get("Location", [])
            for location in location_array:
                json_uri = location.get("Uri")
                if json_uri and "BiosAttributeRegistry" in json_uri and json_uri.endswith(".json"):
                    self.log_box.insert("end", f"[✔] BIOS Registry JSON found: {json_uri}\n")
                    print(f"[✔] BIOS Registry JSON found: {json_uri}")
                    return json_uri
        self.log_box.insert("end", "[!] BIOS Attribute Registry JSON not found.\n\n")
        print("[!] BIOS Attribute Registry JSON not found.")

        return None

    #▶ Attribute
    def dump_bios_registry_txt(self, client, registry_uri, output_path="bios_registry_dump.txt"):
        """
        Dumps BIOS attribute registry grouped by logical MenuPath and sorted by attribute name within each group.
        """
        global registry_block

        # Define shortform mapping and desired output order
        menu_mapping = {
            "MAIN": "Main",
            "ADVC": "Advanced",
            "CHIP": "Chipset",
            "BOOT": "Boot",
            "SECU": "Security",
            "EXIT": "Save & Exit",
            "SERM": "Server Management"
        }
        desired_menu_order = [
            "Main", "Advanced", "Chipset", "Boot",
            "Security", "Save & Exit", "Server Management", "No MenuPath"
        ]

        def compute_menu_path(attribute_name):
            suffix = attribute_name[-5:]
            for code, full_name in menu_mapping.items():
                if code in suffix:
                    return full_name
            return "No MenuPath"

        response = client.get(registry_uri)
        if response.status != 200:
            self.log_box.insert("end", f"Failed to fetch BIOS Registry: {response.status}\n")
            print(f"Failed to fetch BIOS Registry: {response.status}")
            return

        registry_data = response.dict
        attributes = registry_data.get("RegistryEntries", {}).get("Attributes", [])

        # Get current BIOS settings
        bios_settings_uri = "/redfish/v1/Systems/Self/Bios/SD"
        settings_response = client.get(bios_settings_uri)
        if settings_response.status != 200:
            self.log_box.insert("end", f"Failed to fetch BIOS Settings: {settings_response.status}\n")
            print(f"Failed to fetch BIOS Settings: {settings_response.status}")
            current_values = {}
        else:
            current_values = settings_response.dict.get("Attributes", {})

        # Group attributes by MenuPath
        grouped = {}
        for attr in attributes:
            attr_name = attr.get("AttributeName", "N/A")
            menu_path = compute_menu_path(attr_name)
            grouped.setdefault(menu_path, []).append(attr)

        registry_block = {}
        # Write to file in desired menu order
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("==== BIOS Attribute Registry Dump (Grouped by MenuPath) ====\n\n")

            for menu_path in desired_menu_order:
                if menu_path not in grouped:
                    continue
                f.write(f"## Menu Path: {menu_path}\n\n")

                for attr in sorted(grouped[menu_path], key=lambda x: x.get("AttributeName", "")):
                    name = attr.get("AttributeName", "")
                    display = attr.get("DisplayName", "")
                    help_text = attr.get("HelpText", "")
                    type_ = attr.get("Type", "")
                    current_val = current_values.get(name, "")
                    default_val = attr.get("DefaultValue", "")
                    value_options = attr.get("Value", [])

                    enum_display_names = [
                        f"{v.get('ValueName', '')} ({v.get('ValueDisplayName', '')})"
                        for v in value_options
                    ] if isinstance(value_options, list) else []

                    if not enum_display_names and type_ == "Boolean":
                        enum_display_names = self.infer_boolean_enum_options(default_val)

                    f.write(f"▶ Attribute: {name}\n")
                    f.write(f"   - Menu Path     : {menu_path}\n")
                    f.write(f"   - Display Name : {display}\n")
                    f.write(f"   - Type         : {type_}\n")
                    f.write(f"   - Description  : {help_text}\n")
                    f.write(f"   - Current Value   : {current_val}\n")
                    f.write(f"   - Default Value   : {default_val}\n")

                    registry_block[name] = {
                        "Attribute": name,
                        "Type": type_,
                        "Current_Value": current_val,
                        "Menu_Path": menu_path,
                        "Enum Options": enum_display_names
                    }
                    if enum_display_names:
                        f.write(f"   - Enum Options    : {enum_display_names}\n")

                    f.write("\n")


        self.log_box.insert("end", f"[✔] BIOS registry dumped to: {output_path}\n")
        print(f"[✔] BIOS registry dumped to: {output_path}")

        # Call scrollable table generation
        flattened = []
        for group in desired_menu_order:
            if group in grouped:
                for attr in grouped[group]:
                    attr_copy = attr.copy()
                    attr_copy["CurrentValue"] = current_values.get(attr_copy.get("AttributeName", ""), "")
                    flattened.append(attr_copy)

        # Populate the table in Frame 4
        self.populate_attribute_summary(self.tree, flattened)

    #create 2 same txts, including the attributes and its values (Original, edited)
    def dump_bios_settings_txt(self, client, bios_settings_uri="/redfish/v1/Systems/Self/Bios/SD"):
        """
        Fetches BIOS settings and dumps them into two one-liner .txt files:
        - bios_sd_original.txt (reference)
        - bios_sd_edited.txt (for user edits)
        
        Format: Name: Value
        """

        global sd_block

        # login BMC system
        self.client = redfish_client(base_url='https://' + bmc_ip, username=bmc_user, password=bmc_pw)
        self.client.login()

        response = client.get(bios_settings_uri)
        if response.status != 200:
            print(f"Failed to fetch BIOS settings: {response.status}")
            return

        bios_data = response.dict
        attributes = bios_data.get("Attributes", {})


        def write_oneliner(filepath):
            global sd_block

            with open(filepath, "w", encoding="utf-8") as f:
                f.write("==== BIOS Settings Dump ====\n\n")
                for key, value in attributes.items():
                    f.write(f"{key}: {value}\n")
                    # print(key,value)
                    sd_block[key] = {"Attribute Name": key,
                                       "Type":None,
                                       "Current Value": value,
                                       "Enum Options":{}}

            # for items in registry_block.values():
            #     print(items)
        def filling_sd_block():
            global sd_block, registry_block
            # print("herhe", registry_block)
            for attr_name, sd_info in sd_block.items():
                if attr_name in registry_block:
                    reg_info = registry_block[attr_name]
                    # Fill in more detailed info from registry_block
                    sd_info["Type"] = reg_info.get("Type")
                    sd_info["Enum Options"] = reg_info.get("Enum Options", [])
                    sd_info["Menu Path"] = reg_info.get("Menu_Path")
                else:
                    print(f"⚠️ {attr_name} not found in registry_block")
                    self.log_box.insert("end", f"⚠️ {attr_name} not found in registry_block\n")


        # Write both files
        write_oneliner("bios_sd_original.txt")
        sd_block = {}
        write_oneliner("bios_sd_edited.txt")
        filling_sd_block()

        self.tree_filling()
        self.state("zoomed")  # oh yessssss! Zoom da kui!

        self.log_box.insert("end", "[✔] Created 'bios_sd_original.txt' and 'bios_sd_edited.txt'. You may now edit the second one.\n")
        print("[✔] Created 'bios_sd_original.txt' and 'bios_sd_edited.txt'. You may now edit the second one.")

        # Update Frame2 entry boxes with paths
        if hasattr(self, "file_paths"):
            orig_path = os.path.abspath("bios_sd_original.txt")
            edited_path = os.path.abspath("bios_sd_edited.txt")

            self.file_paths["bios_sd_original.txt"].delete(0, "end")
            self.file_paths["bios_sd_original.txt"].insert(0, orig_path)

            self.file_paths["bios_sd_edited.txt"].delete(0, "end")
            self.file_paths["bios_sd_edited.txt"].insert(0, edited_path)



    def infer_boolean_enum_options(self, default_val):
        """
        Given a default value, infer possible options if the type is Boolean
        and value options are not explicitly provided.
        """
        if not isinstance(default_val, str):
            default_val = str(default_val)

        if default_val in ["True", "False"]:
            return ["True", "False"]
        elif default_val in ["true", "false"]:
            return ["true", "false"]
        elif default_val in ["TRUE", "FALSE"]:
            return ["TRUE", "FALSE"]
        elif default_val in ["Enabled", "Disabled"]:
            return ["Enabled", "Disabled"]
        elif default_val in ["enabled", "disabled"]:
            return ["enabled", "disabled"]
        elif default_val in ["1", "0"]:
            return ["1", "0"]
        else:
            return []
        
    # redfish area END ---------------------------------------------------------------------------

    # Frame1 functions area ---------------------------------------------------------------------------

    def load(self): #for loading the previous entries , i.e. bmc ip
        if os.path.exists("saved_credentials.json"):
            try:
                with open("saved_credentials.json", "r") as f:
                    creds = json.load(f)
                    for key, value in creds.items():
                        if key in self.entries:
                            self.entries[key].delete(0, "end")
                            self.entries[key].insert(0, value)
                self.log_box.insert("end", "📥 Entries loaded from file.\n\n")
                print("📥 Entries loaded from file.")
            except Exception as e:
                self.log_box.insert("end", f"❌ Error loading entries: {e}\n\n")
                print(f"❌ Error loading entries: {e}")

    def browse_file(self, target): #for both buttons to get the files' paths for omparison
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")])
        if path:
            self.file_paths[target].delete(0, "end")
            self.file_paths[target].insert(0, path)

    def save(self): # as per mentioned in the names la anything you want me to explain?
        creds = {label: entry.get() for label, entry in self.entries.items()}
        try:
            with open("saved_credentials.json", "w") as f:
                json.dump(creds, f, indent=4)
            self.log_box.insert("end", "[✔] saved_credentials.json opened successfully.\n")
            print("[✔] saved_credentials.json opened successfully.")
        except Exception as e:
            self.log_box.insert("end", f"❌ Error saving entries: {e}\n")
            print(f"❌ Error saving entries: {e}")

        creds = {label: entry.get() for label, entry in self.entries.items()}
        print("Credentials:")
        self.log_box.insert("end", "Credentials:")

        for k, v in creds.items():
            self.log_box.insert("end", f"{k}: {v}\n")
            # print(f"{k}: {v}")
        self.log_box.insert("end", "[✔] Credentials saved successfully.\n")
        print("[✔] Credentials saved successfully.")
        self.print_separate()


    def dump(self): # it's so obvious la ching, is that a necessary to read this?
        global bmc_ip, bmc_user, bmc_pw, os_ip, os_user, os_pw

        # Step 1: Get credentials from entry fields
        bmc_ip = self.entries["BMC IP"].get()
        bmc_user = self.entries["BMC Username"].get()
        bmc_pw = self.entries["BMC Password"].get()
        password_name = self.entries["PW Attribute Name"].get() # 你之前成功用過的欄位名
        old_password = self.entries["Old Password"].get() # 如果之前無密碼就可以空
        new_password = self.entries["New Password"].get() # 可改成從 GUI 輸入

        # Check if any input is blank
        if not bmc_ip or not bmc_user or not bmc_pw:
            self.log_box.insert("end", "❌ BMC IP, Username, and Password cannot be blank.\n\n")
            messagebox.showerror("Input Error", "BMC IP, Username, and Password cannot be blank.")
            return
    
        # Step 2: Login to Redfish
        # Call the dump logic (login + redfish actions)
        self.perform_redfish_dump(bmc_ip, bmc_user, bmc_pw)

    # Frame1 functions area END ---------------------------------------------------------------------------

    # Frame2 functions area ---------------------------------------------------------------------------


    def celebrate_password_success(self):
        # 隨機 emoji 賀詞

        messages = [
            "🎉 恭賀老爺夫人 改密大成！🎊",
            "👑 BIOS 密碼成功！榮登 IT 殿堂之巔！",
            "🔐 龍飛鳳舞，密碼即改！👏",
            "✨ 成功改密，Redfish 也俯首稱臣 😌",
            "🌟 BIOS 密碼更改大吉，萬事勝意！"
        ]

        chosen = random.choice(messages)
        msg_label = ctk.CTkLabel(self, text=chosen, font=ctk.CTkFont(size=18, weight="bold"), text_color="gold")
        msg_label.place(relx=0.5, rely=0.3, anchor="center")

        # 產生閃爍星星動畫
        stars = []

        for _ in range(100):  # 星星數
            label = ctk.CTkLabel(self, text="✨", text_color="yellow", fg_color="transparent")
            x = random.uniform(0.1, 0.9)
            y = random.uniform(0.1, 0.8)
            label.place(relx=x, rely=y, anchor="center")
            stars.append(label)

        def twinkle():
            for star in stars:
                if not star.winfo_exists():
                    continue  # skip if star is already destroyed

                dx = random.uniform(-0.01, 0.01)
                dy = random.uniform(-0.01, 0.01)
                try:
                    new_x = star.winfo_x() / self.winfo_width() + dx
                    new_y = star.winfo_y() / self.winfo_height() + dy
                    star.place_configure(relx=max(0.05, min(0.95, new_x)),
                                        rely=max(0.05, min(0.95, new_y)))
                except:
                    continue  # skip if error occurs
            self.after(200, twinkle)


        twinkle()

        # 3 秒後自動消失
        self.after(3000, lambda: msg_label.destroy())
        self.after(3000, lambda: [star.destroy() for star in stars])

    def kai_sim(self):
        ascii_art = """
    *ੈ✩‧₊˚༺☆༻*ੈ✩‧₊˚*ੈ✩‧₊˚༺☆༻*ੈ✩‧₊˚
    ╔════════════════════════════════════╗
    ║ !!恭喜老爺 賀喜夫人! 改密碼大成功!!   ║
    ╚════════════════════════════════════╝⠀⠀
    *ੈ✩‧₊˚༺☆༻*ੈ✩‧₊˚*ੈ✩‧₊˚༺☆༻*ੈ✩‧₊˚
    """
        self.log_box.insert("end", ascii_art + "\n")
        # self.log_box.insert("end", "🌟 Mission Complete: You just BIOS'd the impossible. 🌟\n\n")
        self.log_box.see("end")  # Scroll to bottom
        # print(ascii_art)

    def change_bios_password(self):
        global bmc_ip, bmc_user, bmc_pw

        bmc_ip = self.entries["BMC IP"].get()
        bmc_user = self.entries["BMC Username"].get()
        bmc_pw = self.entries["BMC Password"].get()
        password_name = self.entries["PW Attribute Name"].get() # 你之前成功用過的欄位名
        old_password = self.entries["Old Password"].get() # 如果之前無密碼就可以空
        new_password = self.entries["New Password"].get() # 可改成從 GUI 輸入

        try:
            client = redfish_client(base_url=f"https://{bmc_ip}", username=bmc_user, password=bmc_pw)
            client.login()
            body = {
                "PasswordName": password_name,
                "OldPassword": old_password,
                "NewPassword": new_password
            }

            response = client.post("/redfish/v1/Systems/Self/Bios/Actions/Bios.ChangePassword", body=body)
            
            if response.status in [200, 204]:
                self.log_box.insert("end", f"[✔] BIOS password {new_password} request sent (204: No Content). Check if it applies after pressing 'reboot'.\n")
                print(f"[✔] BIOS password {new_password} request sent (204: No Content). Check if it applies after pressing 'reboot'.")
                # self.kai_sim()
                # self.celebrate_password_success()
        
            else:
                self.log_box.insert("end", f"❌ : {response.status} - {response.dict}\n")
                print(f"❌ 修改失敗: {response.status} - {response.dict}")

        except Exception as e:
            self.log_box.insert("end", f"❌ Redfish 連線或操作錯誤: {e}\n")
            print(f"❌ Redfish 連線或操作錯誤: {e}")

    def reboot(self):
        global bmc_ip, bmc_user, bmc_pw
        try:
            client = redfish_client(base_url="https://" + bmc_ip, username=bmc_user, password=bmc_pw)
            client.login()

            body = {"ResetType": "PowerCycle"}  # ← 你已確認這是支援的 reset type
            response = client.post("/redfish/v1/Systems/Self/Actions/ComputerSystem.Reset", body=body)

            if response.status in [200, 202, 204]:
                self.log_box.insert("end", "[🔁] System reboot (ForceRestart) triggered successfully.\n")
                print("[🔁] System reboot (ForceRestart) triggered successfully.")
                self.print_separate()
            else:
                self.log_box.insert("end", f"❌ Reboot failed: {response.status}\n{response.text}\n")
                print(f"❌ Reboot failed: {response.status}\n{response.text}")
                self.print_separate()                

        except Exception as e:
            self.log_box.insert("end", f"❌ Reboot error: {e}\n")
            print(f"❌ Reboot error: {e}")
            self.print_separate()

        self.log_box.see("end")
    # Frame2 functions area END ---------------------------------------------------------------------------

    # Frame4 functions area ---------------------------------------------------------------------------
    def populate_attribute_summary(self, parent_frame, attribute_list):

        #read atteibute-value pairs from bios_edited.txt
        original_path="bios_registry_dump.txt"
        revise_path="bios_sd_edited.txt"

        if not os.path.exists(revise_path):
            self.log_box.insert("end", f"❌ File not found: {revise_path}\n")
            return
        if not os.path.exists(revise_path):
            self.log_box.insert("end", f"❌ File not found: {revise_path}\n")
            return

    
    def tree_filling(self):
        global sd_block
        self.tree.delete(*self.tree.get_children())  # Clear existing rows
        for attr_name, sd_info in sd_block.items():
            block = {
                "Attribute": attr_name,
                "Type": sd_info.get("Type", "Unknown"),
                "Value": sd_info.get("Current Value", "[Not Set]"),
                "Enum Options": sd_info.get("Enum Options", [])
            }
            self.insert_treeview_row(block)

        self.log_box.insert("end", f"[✔] Loaded {len(sd_block)} BIOS attributes into Treeview.\n")
        print(f"[✔] Loaded {len(sd_block)} BIOS attributes into Treeview.")
 
    def insert_treeview_row(self, block):
        attr = block.get("Attribute", "N/A")
        type_ = block.get("Type", "Unknown")
        current_val = block.get("Value", "[Not Set]")

        # Clean enum options
        raw_options = block.get("Enum Options", [])

        display_options = []
        display_to_real = {}

        for opt in raw_options:
            if " (" in opt and opt.endswith(")"):
                value_name = opt.split(" (")[0]
                display_options.append(opt)
                display_to_real[opt] = value_name
            else:
                display_options.append(opt)
                display_to_real[opt] = opt

        # Insert row into Treeview
        values = (attr, type_, current_val, current_val)
        self.tree.insert("", "end", values=values)
        self.all_tree_rows.append(values)

        # Store mappings
        self.enum_options_map[attr] = display_options
        if not hasattr(self, "display_to_real_map"):
            self.display_to_real_map = {}
        self.display_to_real_map[attr] = display_to_real



    def on_treeview_double_click(self, event):
        # Identify row and column
        row_id = self.tree.identify_row(event.y)
        col_id = self.tree.identify_column(event.x)

        if not row_id or col_id != '#4':  # Only allow edit on column 4 ("Value")
            return

        # Get bounding box of the cell
        bbox = self.tree.bbox(row_id, col_id)
        if not bbox:
            return

        x, y, width, height = bbox
        values = self.tree.item(row_id, "values")
        if len(values) < 4:
            return

        attr, type_, current_val, val = values
        options = self.enum_options_map.get(attr, [])

        # Destroy old widget if exists
        if hasattr(self, "tree_input_widget") and self.tree_input_widget.winfo_exists():
            self.tree_input_widget.destroy()

        # Dropdown for enum/boolean
        if options:
            var = tk.StringVar(value=val)
            combo = ttk.Combobox(self.tree, values=options, textvariable=var, state="readonly")
            combo.place(x=x, y=y, width=width, height=height)
            combo.focus()

            def on_select(event=None):
                new_val = var.get()
                self.tree.item(row_id, values=(attr, type_, current_val, new_val))
                # Update in all_tree_rows too
                for i, row in enumerate(self.all_tree_rows):
                    if row[0] == attr:
                        self.all_tree_rows[i] = (attr, type_, current_val, new_val)
                combo.destroy()

            combo.bind("<<ComboboxSelected>>", on_select)
            combo.bind("<FocusOut>", lambda e: combo.destroy())
            self.tree_input_widget = combo

        # Entry for manual text input
        else:
            entry = tk.Entry(self.tree)
            entry.insert(0, val)
            entry.place(x=x, y=y, width=width, height=height)
            entry.focus()

            def on_commit(event=None):
                new_val = entry.get()
                self.tree.item(row_id, values=(attr, type_, current_val, new_val))
                # Update in all_tree_rows too
                for i, row in enumerate(self.all_tree_rows):
                    if row[0] == attr:
                        self.all_tree_rows[i] = (attr, type_, current_val, new_val)
                entry.destroy()

            entry.bind("<Return>", on_commit)
            entry.bind("<FocusOut>", on_commit)
            self.tree_input_widget = entry


    def search_treeview(self, keyword):
        keyword = keyword.lower()
        self.tree.delete(*self.tree.get_children())

        for row in self.all_tree_rows:
            attr = row[0].lower()
            if keyword in attr:
                self.tree.insert("", "end", values=row)

    def create_scroll_frame(self, parent_frame):
        # Clear previous
        for widget in parent_frame.winfo_children():
            widget.destroy()

        # Create search bar with placeholder
        search_var = tk.StringVar()
        self.search_entry = ctk.CTkEntry(parent_frame, textvariable=search_var, placeholder_text="Search here...")
        self.search_entry.grid(row=0, column=0, padx=5, pady=(5, 2), sticky="ew", columnspan=2)

        self.search_entry.bind("<KeyRelease>", lambda e: self.search_treeview(search_var.get()))

        # Create a vertical scrollbar
        vsb = ttk.Scrollbar(parent_frame, orient="vertical")
        vsb.grid(row=1, column=1, sticky="ns")

        # Treeview
        self.tree = ttk.Treeview(parent_frame, columns=("attr", "type", "current", "revised"),
                                show="headings", height=25, yscrollcommand=vsb.set)

        vsb.config(command=self.tree.yview)

        self.tree.heading("attr", text="Attribute")
        self.tree.heading("type", text="Type")
        self.tree.heading("current", text="Current Value")
        self.tree.heading("revised", text="Value")

        self.tree.column("attr", width=120, anchor="w")
        self.tree.column("type", width=120, anchor="w")
        self.tree.column("current", width=120, anchor="w")
        self.tree.column("revised", width=320, anchor="w")

        self.tree.bind("<Double-1>", self.on_treeview_double_click)
        self.tree.grid(row=1, column=0, sticky="nsew")

        # Grid config to allow resizing
        parent_frame.grid_columnconfigure(0, weight=1)
        parent_frame.grid_rowconfigure(1, weight=1)





    # Frame4 functions area END ---------------------------------------------------------------------------

    # init area ---------------------------------------------------------------------------
    def __init__(self): # create the window + pre-load previous data
        super().__init__()

        # define area
        self.enum_options_map = {} # Maps attribute name → list of options
        self.all_tree_rows = []

        # Fonts settings
        self.font = ctk.CTkFont(size=13) #context font
        self.entry_font = ctk.CTkFont(size=12) #context font
        self.title_font = ctk.CTkFont(size=20, weight="bold") #title font
        self.header_font = ctk.CTkFont(size=14, weight="bold") #title font
        code_font=ctk.CTkFont(family='Courier New', size=12, weight="bold")
        self.geometry("+0+0")

        # GUI 
        self.title("Redfish tool for changing BIOS TOKEN")  #WINDOW TITLE

        # Frames positions configuration #0=fixed, 1=resizable
        self.grid_rowconfigure(1, weight=1)     # row for frame1 & frame2
        self.grid_rowconfigure(2, weight=1)     # row for frame3
        self.grid_rowconfigure(1, weight=0)     # row 1 fixed height
        # self.grid_rowconfigure(1, weight=1)     # row 1 (where frames live) stretches, (optional: for vertical expanding)
        
        self.grid_columnconfigure(0, weight=0)  # column for frame1
        self.grid_columnconfigure(1, weight=0)  # column for frame2 
        self.grid_columnconfigure(2, weight=1)  # column for frame4     

        # # Title label
        # ctk.CTkLabel(self, text="究竟讀fing 99 , 99fing 定 9 fing fing?", 
        #              font=self.title_font).grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 0), sticky="n")
        
        # create Frame 1 
        self.frame1 = MyFrame(master=self)
        self.frame1.grid(row=1, column=0, padx=(outer_edge, inner_edge), pady=(outer_edge,inner_edge), sticky="news")

        # define labels and entries
        self.entries = {}  # Entry fields dictionary
        field_names = ["BMC IP", "BMC Username", "BMC Password", "PW Attribute Name", "Old Password", "New Password"]  # Field labels
   
        # Create form using grid
        for row_index, name in enumerate(field_names, start=1):
            label = ctk.CTkLabel(self.frame1, text=f"{name}:", font=self.font, anchor="e")
            label.grid(row=row_index, column=0, padx=(outer_edge,inner_edge), pady=(10 if row_index == 1 else 10, 5), sticky="e")

            # entry = ctk.CTkEntry(self.frame1, font=self.font, width=120, show="*" if "Password" in name else "")
            entry = ctk.CTkEntry(self.frame1, font=self.font, width=120)
            entry.grid(row=row_index, column=1, padx=(inner_edge,outer_edge), pady=(10 if row_index == 1 else 10, 5), sticky="ew")

            self.entries[name] = entry 

        # Frame1 inner configuration - Let the inner frame stretch its columns - frame 1 inner
        self.frame1.grid_columnconfigure(0, weight=0)  # label column expands
        self.frame1.grid_columnconfigure(1, weight=0)  # entry column expands

        # Frame 1 - subframe for buttons 
        button_row = len(field_names) + 1

        # Create a subframe for buttons
        self.button_frame = ctk.CTkFrame(self.frame1, fg_color="transparent")
        self.button_frame.grid(row=button_row, column=0, columnspan=2, padx=outer_edge, pady=(inner_edge,outer_edge), sticky="news")

        # Button frame - configuration - Let inner buttons stretch evenly #1=expand, 0=fixed
        self.button_frame.grid_columnconfigure(0, weight=1) # button frame1 col expands
        self.button_frame.grid_columnconfigure(1, weight=1) # button frame1 col expands
        self.button_frame.grid_columnconfigure(2, weight=1) # button frame1 col expands

        # Load button
        ctk.CTkButton(self.button_frame, text="Load", command=self.load, font=self.font, height=30, width=10)\
            .grid(row=0, column=0, padx=(0, 5), sticky="ew")   
         
        # Save Button (middle)
        ctk.CTkButton(self.button_frame, text="Save", command=self.save, font=self.font, height=30, width=10)\
            .grid(row=0, column=1, padx=5, sticky="ew")

        # Dump Button (right)
        ctk.CTkButton(self.button_frame, text="Dump", command=self.dump, font=self.font, height=30, width=10)\
            .grid(row=0, column=2, padx=(inner_edge,0), sticky="ew")
        
        # Create Frame 2
        self.file_paths = {}    # File path entries

        self.frame2 = ctk.CTkFrame(master=self)
        self.frame2.grid(row=1, column=1, padx=(inner_edge), pady=(outer_edge,inner_edge), sticky="ns")

        # create file paths/labels/buttons
        labels = ["Original BIOS:", "Edited BIOS:"]
        files = ["bios_sd_original.txt", "bios_sd_edited.txt"]

        next_row = 0
        for i, (label_text, filename) in enumerate(zip(labels, files)):
            label = ctk.CTkLabel(self.frame2, text=label_text, font=self.font)
            label.grid(row=i, column=0, padx=(outer_edge,inner_edge), pady=10, sticky="e")

            entry = ctk.CTkEntry(self.frame2, font=self.entry_font, width=entry_width)
            entry.grid(row=i, column=1, padx=inner_edge, pady=10, sticky="ew")

            button = ctk.CTkButton(
                self.frame2,
                text="📁",
                width=30,
                height=36,
                font=ctk.CTkFont(size=18, weight="bold"),
                command=lambda t=filename: self.browse_file(t)
            )            
            button.grid(row=i, column=2, padx=(inner_edge,outer_edge), pady=10)
            self.file_paths[filename] = entry
            next_row = i
        next_row+=1  

        self.compare_result_label = ctk.CTkLabel(self.frame2, text="Compared:", font=self.font)
        self.compare_result_label.grid(row=next_row, column=0, padx=(outer_edge,inner_edge), pady=10, sticky="e")

        self.compare_result_entry = ctk.CTkEntry(self.frame2, font=self.font, width=entry_width)
        self.compare_result_entry.grid(row=next_row, column=1, padx=inner_edge, pady=10, sticky="ew")
        self.file_paths["compare_result"] = self.compare_result_entry

        self.compare_result_button = ctk.CTkButton(
            self.frame2,
            text="📁",
            width=30,
            height=36,
            font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda t=filename: self.browse_file("compare_result")
        )            
        self.compare_result_button.grid(row=next_row, column=2, padx=(inner_edge,outer_edge), pady=10)  
        
        next_row+=1

        # Frame 2 inner configuration
        self.frame2.grid_columnconfigure(0, weight=0)  # label column: 0=fixed
        self.frame2.grid_columnconfigure(1, weight=1)  # entry column expands
        self.frame2.grid_columnconfigure(2, weight=0)  # icon column: 0=fixed

        # Create a subframe for buttons
        self.button_frame2 = ctk.CTkFrame(self.frame2, fg_color="transparent")
        self.button_frame2.grid(row=next_row, column=0, columnspan=3, padx=outer_edge, pady=(inner_edge), sticky="ew")
        
        next_row+=1

        # Compare Button
        ctk.CTkButton(self.button_frame2, text="Compare", command=self.compare, font=self.entry_font, height=40)\
            .grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # patch button 
        ctk.CTkButton(self.button_frame2, text="Patch", command=self.patch, font=self.entry_font, height=40)\
            .grid(row=0, column=1, padx=10, pady=10, sticky="ew") 
        
        # Reboot Button
        ctk.CTkButton(self.button_frame2, text="Reboot", command=self.reboot, font=self.entry_font, height=40, hover_color="red")\
            .grid(row=1, column=1, padx=10, pady=10, sticky="ew")
        
        # 改密碼按鈕放喺 self.button_frame2 裡面
        ctk.CTkButton(self.button_frame2, text="Change PW", command=self.change_bios_password, font=self.entry_font, height=40)\
            .grid(row=1, column=0, padx=10, pady=10, sticky="ew")
               
        # Let inner buttons stretch evenly
        self.button_frame2.grid_columnconfigure(0, weight=1)
        self.button_frame2.grid_columnconfigure(1, weight=1)
        self.button_frame2.grid_columnconfigure(2, weight=1)

        # Create Frame 3 - print kui lo mo cuk lai! 
        # bottom full-width frame
        self.frame3 = ctk.CTkFrame(master=self)
        self.frame3.grid(row=2, column=0, columnspan=2, padx=(outer_edge, inner_edge), pady=(inner_edge, outer_edge), sticky="nsew")

        self.frame3.grid_columnconfigure(0, weight=1)  # label column
        self.frame3.grid_rowconfigure(0, weight=1)    

        # define mai frame 3 yong mud 7 font, kui gei leng gar ~ <3
        self.log_box = ctk.CTkTextbox(self.frame3, font=code_font, height=200)
        self.log_box.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create Frame 4 - print kui lo mo cuk lai! 
        self.frame4 = ctk.CTkFrame(master=self)
        self.frame4.grid(row=1, column=2, rowspan=2, padx=(inner_edge,outer_edge), pady=outer_edge, sticky="nsew")
        
        # side panel frame - side angle side, side , side, SIDE!!!!!
        self.frame4.rowconfigure(0, weight=1)
        self.frame4.columnconfigure(0, weight=1)


        self.scroll_frame = ctk.CTkFrame(master=self.frame4)
        self.scroll_frame.grid(row=0,column=0, sticky="news")
        self.create_scroll_frame(self.scroll_frame)
        self.revise_button = ctk.CTkButton(self.frame4, text="Revise", font=self.font, height=40, command=self.revise)\
            .grid(row=2, column=0)
        
        # create the content
        # self.create_scroll(self.frame4)
        # add_background_text(self.frame4)        
        # add_background_text_AIC(self.frame4)

        self.load()  

        # self.after(100, self.center_the_window) #see if you need to centered the window





    # init area END ---------------------------------------------------------------------------

# function area END ---------------------------------------------------------------------------


# main area ---------------------------------------------------------------------------

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# **  UI  **
# Set appearance mode and theme
ctk.set_appearance_mode("System")  # "Light", "Dark", "System"
# ctk.set_default_color_theme("themes/cherry.json")
ctk.set_default_color_theme("themes/rime.json")

if __name__ == "__main__":

    # show_intro_popup()

    app = CredentialApp()
    app.mainloop()


# main area END ---------------------------------------------------------------------------



# JFF area =b -------
def show_intro_popup():
    # Create a temporary window
    splash = tk.Tk()
    splash.title("Introducing...")

    # Optional: make it undecorated (no title bar)
    splash.overrideredirect(True)

    # Position and size
    width, height = 600, 400
    screen_w = splash.winfo_screenwidth()
    screen_h = splash.winfo_screenheight()
    x = int((screen_w / 2) - (width / 2))
    y = int((screen_h / 2) - (height / 2))
    splash.geometry(f"{width}x{height}+{x}+{y}")

    # Message content
    label = tk.Label(
        splash,
        text=(
            "🎬 This glorious mess is \n"
            "proudly brought to you by 飯桶 ._. \n\n"
            "and\n\n"
             "ChatGPT!\n\n"
            "Oops — not really ChatGPT.\n"
             "It did great.\n"
            "I’m responsible for the chaos =b"
        ),
        font=("Segoe UI", 15),
        justify="center",
        wraplength=600,
        padx=20,
        pady=20
    )
    label.pack(expand=True)

    # Auto-close after 3 seconds (3000 ms)
    splash.after(7000, splash.destroy)
    splash.mainloop()

def add_background_text_chiikawa(target_frame):
    ascii_art = """
⠀⠀⠀⠀⠀⠀⢀⡞⠹⣦⠰⡞⠙⣆⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢴⠀⠀⣿⠐⡇⠀⢻⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⠀⠀⣿⢸⡇⠀⢸⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⢀⡸⣄⠀⣿⣨⡇⠀⣟⡀⠀⠀⠀⠀⠀
⠀⠀⢠⡶⠚⠉⢁⡀⠀⠀⠀⠀⠀⡈⠉⠙⠲⣤⡀⠀
⢀⡶⠋⠀⢀⠔⠉⠀⠀⠀⠀⠀⠀⠈⠑⢄⠀⠈⠻⡄
⣾⠁⠀⠀⠈⠀⣠⣂⡄⠀⠀⠀⣔⣢⠀⠈⠀⠀⠀⢹
⡇⠀⠀⢠⣠⣠⡌⠓⠁⠀⡀⠀⠙⠊⡄⢀⣀⠀⠀⢸
⢷⡀⠀⠈⠁⠁⠀⠀⠈⠓⡓⠂⠀⠀⠉⠈⠁⠀⠀⡼
⠈⠳⣄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⡞⠁
⠀⠀⢾⠀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⢸⠀⠀
⠀⠀⠈⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡾⠊⠁⠀
⠀⠀⠀⠘⣇⢀⡀⠀⠀⠀⠀⠀⠀⠀⠀⡀⣷⠀⠀⠀
⠀⠀⠀⠀⢿⣼⠉⠉⠙⠛⠛⠛⠛⠉⢹⣁⠟⠀⠀⠀"""

    bg_label = ctk.CTkLabel(
        target_frame,
        text=ascii_art,
        font=("Arial", 24, "bold"),
        text_color="#CCCCCC",
        fg_color="transparent",
        anchor="center",
        justify="center"
    )
    bg_label.place(relx=0.5, rely=0.5, anchor="center")

def add_background_text_AIC(target_frame):
    ascii_art = """
⠀⠀⠀⣠⣤⣤⣤⣤⣄⠀⠀⠀  ⣿⣿⡇⠀⠀⣠⣤⣤⣤⣤⣤⣤⣤⣤⡄
⠀⣠⣾⣿⣿⠿⠿⢿⣿⣷⣄⠀⠀⣿⣿⡇⢠⣾⣿⣿⠿⠿⠿⠿⠿⠿⠿⠃
⢸⣿⣿⠟⠁⠀⠀⠀⠙⣿⣿⡇⠀⣿⣿⡇⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣿⣿⣀⣀⣀⣀⣀⣀⣿⣿⡇ ⣿⣿⡇⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇ ⣿⣿⡇⢸⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣿⣿  ⠀⠀⠀⠀⠀⣿⣿⣿⠀⣿⣿⡇⠸⣿⣿⣷⣤⣤⣤⣤⣤⣤⣤⡀
⠸⠿⠿ ⠀ ⠀⠀⠀⠀⠿⠿⠿⠀⠿⠿⠇⠀⠈⠻⠿⠿⠿⠿⠿⠿⠿⠿⠇"""

    bg_label = ctk.CTkLabel(
        target_frame,
        text=ascii_art,
        font=("Arial", 24, "bold"),
        # text_color="#CCCCCC",
        text_color="white",
        fg_color="transparent",
        anchor="center",
        justify="center"
    )
    bg_label.place(relx=0.5, rely=0.5, anchor="center")

# JFF area END =(


