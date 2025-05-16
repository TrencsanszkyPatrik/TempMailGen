import requests
import tkinter as tk
from tkinter import messagebox, scrolledtext
import secrets

BASE_URL = "https://api.mail.tm"
session = requests.Session()
token = None
account_email = None
account_password = "password123"

def create_account():
    global token, account_email

    response = session.get(BASE_URL + "/domains")
    domains = response.json()["hydra:member"]
    if not domains:
        messagebox.showerror("Error", "No available domain found.")
        return
    domain = domains[0]["domain"]

    email = f"user{secrets.token_hex(4)}@{domain}"

    payload = {
        "address": email,
        "password": account_password
    }
    r = session.post(BASE_URL + "/accounts", json=payload)
    if r.status_code == 201:
        account_email = email
        email_label.config(text=f"{account_email}")
        login()
    else:
        print(f"Error: {r.status_code}, response: {r.text}")
        messagebox.showerror("Error", f"Failed to create email.\n\n{r.text}")

def login():
    global token
    payload = {
        "address": account_email,
        "password": account_password
    }
    r = session.post(BASE_URL + "/token", json=payload)
    if r.status_code == 200:
        token = r.json()["token"]
        list_messages()
    else:
        print(f"Error: {r.status_code}, response: {r.text}")
        messagebox.showerror("Error", "Failed to login.")

def list_messages():
    if not token:
        messagebox.showerror("Error", "First create an email address!")
        return
    headers = {"Authorization": f"Bearer {token}"}
    r = session.get(BASE_URL + "/messages", headers=headers)
    if r.status_code == 200:
        messages_list.delete(0, tk.END)
        messages = r.json()["hydra:member"]
        if not messages:
            messages_list.insert(tk.END, "Nincs új levél.")
        for msg in messages:
            messages_list.insert(tk.END, f"{msg['from']['address']} | {msg['subject']}")
    else:
        print(f"Error: {r.status_code}, response: {r.text}")
        messagebox.showerror("Error", "Failed to retrieve messages.")

def copy_email_to_clipboard():
    if account_email:
        root.clipboard_clear()
        root.clipboard_append(account_email)
        root.update()
        messagebox.showinfo("Copied!", "The email address has been copied to the clipboard.")
    else:
        messagebox.showwarning("Attention", "First create an email address!")


def show_message_content(event=None):
    selected = messages_list.curselection()
    if not selected:
        return
    index = selected[0]

    headers = {"Authorization": f"Bearer {token}"}
    r = session.get(BASE_URL + "/messages", headers=headers)
    if r.status_code != 200:
        print(f"Error: {r.status_code}, response: {r.text}")
        messagebox.showerror("Error", "Failed to retrieve messages.")
        return

    messages = r.json()["hydra:member"]
    if index >= len(messages):
        messagebox.showerror("Error", "Invalid message index.")
        return

    message_id = messages[index]["id"]
    r = session.get(BASE_URL + f"/messages/{message_id}", headers=headers)
    if r.status_code == 200:
        content = r.json()["text"]
        message_content.delete(1.0, tk.END)
        message_content.insert(tk.END, content)
    else:
        print(f"Error: {r.status_code}, response: {r.text}")
        messagebox.showerror("Error", "Failed to open message.")

# GUI setup
root = tk.Tk()
root.title("Temporary Email Manager (Mail.tm)")
root.geometry("850x600")
root.configure(bg="#f0f0f0")

title_label = tk.Label(root, text="Temporary Email Manager", font=("Helvetica", 20, "bold"), bg="#f0f0f0")
title_label.grid(row=0, column=0, columnspan=3, pady=10)

email_frame = tk.LabelFrame(root, text="Current email address", font=("Helvetica", 12, "bold"), padx=10, pady=10)
email_frame.grid(row=1, column=0, columnspan=3, pady=10, sticky="ew", padx=10)

email_label = tk.Label(email_frame, text="Email address: ", font=("Helvetica", 14))
email_label.pack(side=tk.LEFT, padx=5)

copy_button = tk.Button(email_frame, text="Copy", command=lambda: copy_email_to_clipboard(), bg="#e0e0e0", font=("Helvetica", 10))
copy_button.pack(side=tk.RIGHT, padx=5)


email_label = tk.Label(email_frame, text="No email address", font=("Helvetica", 14))
email_label.pack()

create_button = tk.Button(root, text="New temporary email", command=create_account, width=25, height=2, bg="#4caf50", fg="white", font=("Helvetica", 12))
create_button.grid(row=2, column=0, padx=10, pady=5)

refresh_button = tk.Button(root, text="Refresh messages", command=list_messages, width=25, height=2, bg="#2196f3", fg="white", font=("Helvetica", 12))
refresh_button.grid(row=2, column=1, padx=10, pady=5)



messages_list = tk.Listbox(root, width=60, height=15, font=("Helvetica", 11))
messages_list.grid(row=3, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")
messages_list.bind("<<ListboxSelect>>", show_message_content)

scrollbar = tk.Scrollbar(root)
scrollbar.grid(row=3, column=2, sticky="ns", pady=10)

messages_list.config(yscrollcommand=scrollbar.set)
scrollbar.config(command=messages_list.yview)

content_label = tk.Label(root, text="📨 Message content:", font=("Helvetica", 13, "bold"), bg="#f0f0f0")
content_label.grid(row=4, column=0, columnspan=3, pady=(20, 5))

message_content = scrolledtext.ScrolledText(root, width=95, height=10, font=("Helvetica", 11))
message_content.grid(row=5, column=0, columnspan=3, padx=10, pady=5)

root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=1)
root.grid_columnconfigure(2, weight=0)

root.mainloop()
