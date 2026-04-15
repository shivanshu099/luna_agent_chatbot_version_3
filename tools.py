
import cv2
import time
import uuid
from langchain.tools import tool
import requests
from bs4 import BeautifulSoup
import pyautogui
from PIL import Image
import pytesseract
import os
import json
from datetime import datetime
import webbrowser
import pygame
import platform
from pathlib import Path
from termcolor import colored
import subprocess
from dotenv import load_dotenv

#________________________________vision_tool________________________________________________
@tool
def capture_me(filename:str)->str:
    """open the webcam, capture a single image and save it as a PNG file. it takes the filename as input without extension and then it will return the unique filename"""
    camera=cv2.VideoCapture(0)
    if not camera.isOpened():
        return "could not open webcam"
    ret,frame = camera.read()
    if not ret:
         return "Failed to grab frame"
    time.sleep(2)
    cv2.imshow("heeeee",frame)
    cv2.waitKey(2000)
    image_name=filename+str(uuid.uuid4())+".png"
    cv2.imwrite(image_name,frame)
    camera.release()
    cv2.destroyAllWindows()
    return f"successfully captured the image as {image_name}"

@tool
def latest_news(limit:int)->list:
    """this latest_news tool is used to get latest news from Google there is limit to input to get how many news"""
    try:
        url="https://news.google.com/topics/CAAqJQgKIh9DQkFTRVFvSUwyMHZNRE55YXpBU0JXVnVMVWRDS0FBUAE?hl=en-IN&gl=IN&ceid=IN%3Aen"
        headers={"User-Agent":"Mozilla/5.0"}
        response=requests.get(url,headers)
        soup=BeautifulSoup(response.text,"html.parser")
        links=soup.find_all("a",class_="gPFEn")
        news=[]
        for tag in links[:limit]:
            title = tag.text.strip()
            relative_link = tag["href"]
            full_link = f"https://news.google.com{relative_link[1:]}" if relative_link.startswith('.') else relative_link
            #print("Title:",title)
            #print("Link",full_link)
            #print("-"*40)
            news.append(title)
        return news
    except Exception as e:
        return f"an error occurred: {e}"

@tool
def capture_screenshot(filename:str)->str:
    """this fucntion used to capture the screenshot of system and save into png format and return the unique filename"""
    try:
        un_filename=filename+".png"
        if os.path.exists(un_filename):
            un_filename=filename+"_"+str(uuid.uuid4())+".png"
        time.sleep(2)
        screenshot = pyautogui.screenshot()
        screenshot.save(un_filename)
        return un_filename
    except Exception as e:
        return f"an error occurred: {e}"


@tool
def image_to_text(filename: str, lang: str = "eng") -> str:
    """
    Extracts and returns text from an image file using OCR, with preprocessing.

    Parameters:
    - filename (str): Path to the image file.
    - lang (str): Language code for OCR (default is 'eng').

    Returns:
    - str: Extracted text from the image.
    """
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    try:
        image=cv2.imread(filename)
        if image is None:
            return f"Error: could not read file {filename}"
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        text=pytesseract.image_to_string(gray,lang=lang)
        return text.strip()
    except Exception as e:
        return f"Error processing image: {str(e)}"

#__________________________todo_list_tool__________________________

file_path="todo_list.json"    
def read_todo_list():
    """
    Read the todo list from the JSON file.

    Returns:
        dict: The dictionary containing tasks.
              If file is empty or not found, returns {"tasks": []}.
    """
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # If the file doesn't exist or is corrupted, return an empty structure
        return {"tasks": []}


def save_todos(data):
    """
    Save the todo list into the JSON file.

    Args:
        data (dict): A dictionary containing the tasks to save.
    """
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)

@tool
def todo_add(task: str, time: str = None):
    """
    Add a new task to the todo list.

    Args:
        task (str): The description of the task.
        time (str, optional): A specific time in ISO format. 
                              If not provided, current datetime is used.
    """
    todos = read_todo_list()

    # Use current time if no time is provided
    if not time:
        time = datetime.now().isoformat()

    # New task structure
    new_task = {
        "task": task,
        "time": time,
    }

    # Append new task into list
    todos["tasks"].append(new_task)

    # Save the updated list
    save_todos(todos)


@tool
def todo_list():
    """
    Retrieve and display all tasks in the todo list.

    Returns:
        list: A list of all tasks with their index, task description, and time.
    """
    todos = read_todo_list()
    task_list = todos.get("tasks", [])

    # Format tasks for display
    formatted_tasks = []
    for idx, item in enumerate(task_list, start=1):
        formatted_tasks.append({
            "id": idx,
            "task": item["task"],
            "time": item["time"]
        })

    return formatted_tasks

@tool
def todo_remove(index: int):
    """
    Remove a task from the todo list by its index.

    Args:
        index (int): The 1-based index of the task to remove.

    Returns:
        bool: True if task was removed, False if index was invalid.
    """
    todos = read_todo_list()
    task_list = todos.get("tasks", [])

    # Check if index is valid
    if 1 <= index <= len(task_list):
        task_list.pop(index - 1)  # remove task
        todos["tasks"] = task_list
        save_todos(todos)
        return True
    else:
        return False
    
@tool
def current_time()->str:
    """this function is used for returning the current time in iso format it does not takes any input but return time in str"""
    time = datetime.now().isoformat()
    return time
#_________________________________web_tool_____________________________
@tool
def open_website(url:str):
    """
    Open a given URL in the default web browser.

    Args:
        url (str): The website link to open.
    Returns:
        str: Confirmation message.
    """
    if not url.startswith("http://") and not url.startswith("https://"):
        url="https://"+url
        
    def _open():
        webbrowser.open(url)
        
    import threading
    threading.Thread(target=_open).start()
    return f"opened website: {url}"
#____________________________persnal_info__________________

@tool
def load_persnal_info():
    """
    this function is used to  store persnal information in json file and return the data as dictionary
    it contains many information
    Returns:
        dict: A dictionary containing personal information if the file exists,
              otherwise an empty dictionary.
    """
    if not os.path.exists("persnal_info.json"):
        return {}
    with open("persnal_info.json","r") as f:
        return json.load(f)
    
#________________________________play_music_____________________


@tool
def music_folder_list(folder: str) -> list:
    """
    List all music files (MP3/WAV) in the given folder.

    Args:
        folder (str): Path to the music folder.

    Returns:
        list: Sorted list of music filenames (not full paths).
    """

    # Validate folder exists
    if not os.path.exists(folder):
        return ["Error: Folder not found"]

    # Validate it's a directory
    if not os.path.isdir(folder):
        return ["Error: Provided path is not a folder"]

    try:
        # List only mp3 and wav files (ignore hidden/system files)
        music_files = [
            f for f in os.listdir(folder)
            if f.lower().endswith((".mp3", ".wav")) and not f.startswith(".")
        ]

        # Sort alphabetically for cleaner output
        return sorted(music_files)

    except Exception as e:
        return [f"Error: {str(e)}"]
@tool
def play_sound(file: str) -> str:
    """
    Play an audio file (MP3 or WAV).

    Args:
        file (str): Full path to the audio file.

    Returns:
        str: Status message.
    """
    # Check file exists
    if not os.path.isfile(file):
        return f"Error: File '{file}' not found."

    try:
        system_platform = platform.system()

        if system_platform == "Windows":
            os.startfile(file)

        elif system_platform == "Darwin":  # macOS
            subprocess.Popen(["open", file])

        else:  # Linux
            subprocess.Popen(["xdg-open", file])

        return f"Playing sound: {os.path.basename(file)}"

    except Exception as e:
        return f"Error playing sound: {str(e)}"

@tool
def open_image(file_path: str):
    """
    Open an image file using the default image viewer of the operating system.

    Args:
        file_path (str): Path to the image file to open.

    Returns:
        None
    """
    path = Path(file_path)

    # Check if file exists
    if not path.is_file():
        print(colored(f"❌ File not found: {file_path}", "red"))
        return

    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)  # Windows default
        elif system == "Darwin":  # macOS
            os.system(f"open '{path}'")
        else:  # Linux
            os.system(f"xdg-open '{path}'")
        print(colored(f"✅ Opened image: {file_path}", "green"))
    except Exception as e:
        print(colored(f"Error opening image: {e}", "red"))


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

load_dotenv()
MY_EMAIL=os.getenv("MY_EMAIL")
MY_APP_NAME=os.getenv("MY_APP_NAME")
MY_APP_PASSWORD=os.getenv("MY_APP_PASSWORD")

@tool
def send_email(reciver_email:str,subject:str,body:str)->str:
    """this function is used to send email it takes reciver_email,subject,body as input and return the status of email"""
    msg=MIMEMultipart()
    msg["FROM"]=MY_EMAIL
    msg["TO"]=reciver_email
    msg["Subject"]=subject
    msg.attach(MIMEText(body,"plain"))
    try:
        with smtplib.SMTP("smtp.gmail.com",587) as server:
            server.starttls()
            server.login(MY_EMAIL,MY_APP_PASSWORD)
            server.send_message(msg)
        return "email has been sent"
    except Exception as e:
        return f"an error occurred: {e}"

@tool
def send_email_with_image(reciver_email:str,subject:str,body:str,image_path:str)->str:
    """this function is used to send email and image as attachement it takes reciver_email,subject,body,image_path as input and return the status of email"""

    msg=MIMEMultipart()
    msg["FROM"]=MY_EMAIL
    msg["TO"]=reciver_email
    msg["Subject"]=subject
    msg.attach(MIMEText(body,"plain"))
    try:
        if os.path.exists(image_path):
            with open(image_path,"rb") as img:
                image=MIMEImage(img.read())
                image.add_header("Content-Disposition",f"attachment; filename={os.path.basename(image_path)}")
                msg.attach(image)
        else:
            return f"Error: image file '{image_path}' not found."
        with smtplib.SMTP("smtp.gmail.com",587) as server:
            server.starttls()
            server.login(MY_EMAIL,MY_APP_PASSWORD)
            server.send_message(msg)
        return "email has been sent"
    except Exception as e:
        return f"an error occurred: {e}"
#________________________________tikinhter hidden overlay____________________

import tkinter as  tk
from threading import Thread
from multiprocessing import Process
class TransparentOverlay:
    def __init__(self, text, width=400, height=200, alpha=0.7):
        self.text = text
        self.width = width
        self.height = height
        self.alpha = alpha

    def run(self):
        root = tk.Tk()

        # setup window
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", self.alpha)

        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - self.width) // 2
        y = (screen_height - self.height) // 2
        root.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # close on click or esc
        root.bind("<Button-1>", lambda e: root.destroy())
        root.bind("<Escape>", lambda e: root.destroy())

        # scrollable text
        frame = tk.Frame(root, bg="black")
        frame.pack(expand=True, fill="both", padx=10, pady=10)
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(
            frame,
            yscrollcommand=scrollbar.set,
            font=("Arial", 16),
            bg="black",
            fg="white",
            wrap="word"
        )
        text_widget.insert("1.0", self.text)
        text_widget.config(state="disabled")
        text_widget.pack(expand=True, fill="both", padx=10, pady=10)
        scrollbar.config(command=text_widget.yview)

        root.mainloop()

@tool
def hidden_screen_overlay(text:str)->str:
    """this function is used to display the text on  hidden screen as overlay it takes text as input and return the status of overlay"""
    overlay=TransparentOverlay(text=text)
    #overlay.run
    p=Process(target=overlay.run)
    p.start()
    return f"overlay display with is active"

import asyncio
from playwright.async_api import async_playwright
from typing import List, Dict

from pydantic import BaseModel, Field

class PlacesSearchInput(BaseModel):
    query: str = Field(description="Search query for finding locations, e.g., 'best food stalls near Kanpur'")

@tool("search_google_maps", args_schema=PlacesSearchInput)
def search_google_maps(query: str) -> list:
    """
    Searches Google Maps for places matching the given query and returns a list of places.
    """
    async def _run_playwright():
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Step 1: open google maps search
            base_url = "https://www.google.com/maps/search/"
            query_encoded = "+".join(query.split())
            full_url = base_url + query_encoded

            await page.goto(full_url, timeout=60000)
            await page.wait_for_timeout(4000)

            results = []

            for _ in range(5):
                # Correct selector
                items = await page.query_selector_all(".Nv2PK")

                for item in items:
                    name_el = await item.query_selector(".qBF1Pd")
                    rating_el = await item.query_selector(".MW4etd")
                    address_el = await item.query_selector(".W4Efsd")

                    name = await name_el.inner_text() if name_el else "N/A"
                    rating = await rating_el.inner_text() if rating_el else "N/A"
                    address = await address_el.inner_text() if address_el else "N/A"

                    place = {
                        "name": name,
                        "rating": rating,
                        "address": address
                    }

                    if place not in results:
                        results.append(place)

                # Scroll down
                await page.mouse.wheel(0, 2000)
                await page.wait_for_timeout(1500)

            await browser.close()
            return results
            
    return asyncio.run(_run_playwright())



@tool
def read_directory(path: str = ".") -> list:
    """
    List all files and folders in a given directory path.
    Args:
        path (str): The directory path to read. Defaults to the current directory.
    Returns:
        list: A list of file and folder names in the directory, or an error message.
    """
    try:
        if not os.path.exists(path):
            return [f"Error: Path '{path}' does not exist."]
        if not os.path.isdir(path):
            return [f"Error: '{path}' is not a directory."]
        return os.listdir(path)
    except Exception as e:
        return [f"Error reading directory: {e}"]

@tool
def open_file(file_path: str) -> str:
    """
    Open any file using the default application of the operating system.
    Args:
        file_path (str): The path to the file to open.
    Returns:
        str: Status message.
    """
    path = Path(file_path)
    if not path.exists():
        return f"Error: File or directory '{file_path}' not found."
        
    try:
        system = platform.system()
        if system == "Windows":
            os.startfile(path)
        elif system == "Darwin":
            subprocess.Popen(["open", str(path)])
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return f"Successfully opened: {file_path}"
    except Exception as e:
        return f"Error opening file: {e}"

#________________________________memory_tools_____________________
import chromadb

# Initialize persistent ChromaDB client
_chroma_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luna_memory_db")
_chroma_client = chromadb.PersistentClient(path=_chroma_db_path)
_memory_collection = _chroma_client.get_or_create_collection(
    name="luna_memories",
    metadata={"hnsw:space": "cosine"}
)

@tool
def save_memory(content: str, category: str = "general") -> str:
    """
    Save an important piece of information to Luna's long-term memory.
    Use this when the user shares personal details, preferences, important facts,
    or anything worth remembering for future conversations.

    Args:
        content (str): The information to remember (e.g., "User's name is Shivanshu",
                       "User likes Python programming", "User's birthday is March 15").
        category (str): Category of the memory. Examples: 'personal', 'preference',
                        'fact', 'work', 'general'. Defaults to 'general'.

    Returns:
        str: Confirmation that the memory was saved.
    """
    memory_id = f"mem_{uuid.uuid4().hex[:12]}"
    timestamp = datetime.now().isoformat()

    _memory_collection.add(
        documents=[content],
        metadatas=[{"category": category, "timestamp": timestamp}],
        ids=[memory_id]
    )

    return f"Memory saved: '{content}' [category: {category}]"


@tool
def search_memory(query: str, limit: int = 5) -> list:
    """
    Search Luna's long-term memory for relevant information.
    Use this to recall things the user has told you before, like their name,
    preferences, past conversations, or any stored facts.

    Args:
        query (str): What to search for (e.g., "user's name", "favorite food",
                     "birthday", "work details").
        limit (int): Maximum number of results to return. Defaults to 5.

    Returns:
        list: A list of matching memories with their content, category, and timestamp.
    """
    count = _memory_collection.count()
    if count == 0:
        return ["No memories stored yet."]

    # Don't request more results than exist
    n = min(limit, count)

    results = _memory_collection.query(
        query_texts=[query],
        n_results=n
    )

    memories = []
    if results and results["documents"]:
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            memories.append({
                "memory": doc,
                "category": meta.get("category", "general"),
                "saved_at": meta.get("timestamp", "unknown")
            })

    return memories if memories else ["No relevant memories found."]


@tool
def view_all_memories(limit: int = 20) -> list:
    """
    View all stored memories in Luna's long-term memory.
    Use this when the user asks what you remember about them or wants to see all saved memories.

    Args:
        limit (int): Maximum number of memories to return. Defaults to 20.

    Returns:
        list: A list of all stored memories with content, category, and timestamp.
    """
    count = _memory_collection.count()
    if count == 0:
        return ["No memories stored yet."]

    n = min(limit, count)

    all_data = _memory_collection.get(
        limit=n,
        include=["documents", "metadatas"]
    )

    memories = []
    for doc, meta in zip(all_data["documents"], all_data["metadatas"]):
        memories.append({
            "memory": doc,
            "category": meta.get("category", "general"),
            "saved_at": meta.get("timestamp", "unknown")
        })

    return memories


def tool_define():
    return [
    capture_me,
    latest_news,
    capture_screenshot,
    image_to_text,
    todo_add,
    todo_list,
    todo_remove,
    current_time,
    open_website,
    load_persnal_info,
    music_folder_list,
    play_sound,
    open_image,
    send_email,
    send_email_with_image,
    hidden_screen_overlay,
    search_google_maps,
    read_directory,
    open_file,
    save_memory,
    search_memory,
    view_all_memories
    ]



if __name__=="__main__":
    #print(latest_news())
    #capture_screenshot()
    #re=send_email_with_image("kshivansh.knp@gmail.com","this is subject just for fun ","this is body of email just for fun i try to send email to myself using python  smtp thanks for you reading hope you are fine shivanshu ",r"C:\Users\knath\OneDrive\Pictures\Screenshots\yumi_screenshot.png")
    #hidden_screen_overlay("this is just for testing the overlay screen")
    print(load_persnal_info())




















