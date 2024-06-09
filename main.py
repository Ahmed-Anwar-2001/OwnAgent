import eel
from queue import Queue
import pyautogui
import time
import mouse, keyboard
import json
from keyboard import KeyboardEvent
from collections import namedtuple
from mouse import MoveEvent, WheelEvent, ButtonEvent
from PyQt5.QtWidgets import QWidget, QApplication, QRubberBand, QMessageBox
from PyQt5.QtGui import QMouseEvent, QPixmap
from PyQt5.QtCore import Qt, QPoint, QRect, QStandardPaths
import sys
import os, re
from pathlib import Path
import shutil
import requests
from dotenv import load_dotenv

#Agent
from crewai import Agent, Task, Crew, Process, tools
from crewai_tools import BaseTool
from langchain.tools import tool

# Set up API keys
os.environ["SERPER_API_KEY"] = os.getenv('SERPER_API_KEY')
os.environ["OPENAI_API_BASE"] = os.getenv('OPENAI_API_BASE')
os.environ["OPENAI_MODEL_NAME"] = os.getenv('OPENAI_MODEL_NAME')
os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')


from openai import OpenAI


load_dotenv()

def query(payload):
	response = requests.post("https://api-inference.huggingface.co/models/mistralai/Mixtral-8x7B-Instruct-v0.1", headers={"Authorization": "Bearer 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"}, json=payload)
	return response.json()


eel.init('web')
tasks = None


def copy_file(src, dst):
    try:
        shutil.copy(src, dst)
    except Exception as e:
        print(f"Error copying file: {e}")

def file_exists(directory, filename):
    file_path = Path(directory) / filename
    return file_path.is_file()

def separate_tasks(interactions):  
    double = False
    c = 1  
    tasks = {}
    q2 = None
    count = 1 
    for i in interactions:
        if q2 is None:
            q2 = [i]
        elif isinstance(i, q2[-1].__class__):
            if isinstance(i, mouse._mouse_event.ButtonEvent) and i.event_type=='up':
                if double == True:
                    q2.append(i)
                    double = False
                else:
                    q2.append([i, f"screenshot_{c}.png"])
                    c+=1
            elif isinstance(i, mouse._mouse_event.ButtonEvent) and i.event_type=='down':
                q2.append(i)
                double = True
                c+=2
            else:
                q2.append(i)

        else:
            tasks[count] = q2
            if isinstance(i, mouse._mouse_event.ButtonEvent) and i.event_type=='double':
                double = True
                q2 = [i]
                c+=2
            else:
                q2 = [i]
            count+=1
    return tasks

def filter_input1(arr):
    final = []
    temp = []
    q3 = []
    for i in range(len(arr)-1):
        if arr[i].event_type=='down' and arr[i+1].event_type!='up':
            if arr[i].name=='shift' and (len(arr[i+1].name)==1 or arr[i+1].name=='enter'):
                temp.append(arr[i])
                continue
            if len(q3)==0:
                if len(temp)!=0:
                    final.append(temp) 
                temp = [arr[i]]
            else:
                temp.append(arr[i])
            q3.append(arr[i].name)
        else:
            if len(q3)==0:
                temp.append(arr[i])
            else:
                if arr[i].name in q3 and arr[i].event_type=='up':
                    q3.remove(arr[i].name)
                    temp.append(arr[i])
                    if len(q3)==0:
                        if len(temp)!=0:
                            final.append(temp) 
                        temp = []
                else:
                    temp.append(arr[i])
    final.append((temp+[arr[-1]]))
    return final


def filter_input(arr):
    return [arr]

def serialize_data(tasks, filename):
    serialized_dict = {}
    for key, custom_objs in tasks.items():
        if isinstance(custom_objs[0], list):
            serialized_dict[key] = []
            for i in range(len(custom_objs)):
                serialized_objs = []
                for obj in custom_objs[i]:
                    if isinstance(obj, str):
                        serialized_objs.append(obj)
                    else:
                        serialized_objs.append(obj.__dict__)
                serialized_dict[key].append(serialized_objs)
        else:
            serialized_objs = custom_objs
            serialized_dict[key] = serialized_objs

    # Specify the file path where you want to save the JSON file
    file_path = f"web/tasks/"+filename+".json"

    # Open the file in write mode
    with open(file_path, "w") as json_file:
        # Use json.dump() to write the dictionary to the file
        json.dump(serialized_dict, json_file, indent=2)

    print("JSON file created successfully.")


def delete_files_in_directory(directory_path):
   try:
     files = os.listdir(directory_path)
     for file in files:
       file_path = os.path.join(directory_path, file)
       if os.path.isfile(file_path):
         os.remove(file_path)
     print("All files deleted successfully.")
   except OSError:
     print("Error occurred while deleting files.")


path = {'default':"Reset"}
c1 = 1
class Capture(QWidget):

    def __init__(self, main_window,files='none'):
        super().__init__()
        self.file = files
        self.main = main_window
        self.setMouseTracking(True)
        desk_size = QApplication.desktop()
        self.setGeometry(0, 0, desk_size.width(), desk_size.height())
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowOpacity(0.15)

        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = QPoint()

        QApplication.setOverrideCursor(Qt.CrossCursor)
        screen = QApplication.primaryScreen()
        rect = QApplication.desktop().rect()

        self.imgmap = screen.grabWindow(
            QApplication.desktop().winId(),
            rect.x(), rect.y(), rect.width(), rect.height()
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = event.pos()
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())
            self.rubber_band.show() 

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubber_band.setGeometry(QRect(self.origin, event.pos()).normalized())

    def mouseReleaseEvent(self, event):
        global path, c1
        if event.button() == Qt.LeftButton:
            self.rubber_band.hide()
            
            rect = self.rubber_band.geometry()
            cropped_img = self.imgmap.copy(rect)
            QApplication.restoreOverrideCursor()
            
            # Define the path to the new folder
            project_dir = os.path.dirname(os.path.abspath(__file__))
            save_dir = os.path.join(project_dir, 'web', 'images', 'changed_clicks')
            
            # Ensure the directory exists
            if not os.path.exists(save_dir):
                os.makedirs(save_dir)
            if c1==1:
                delete_files_in_directory('web/images/changed_clicks')

            file_path = os.path.join(save_dir, f"screenshot{c1}.png")
            
            if not cropped_img.save(file_path, "PNG"):
                QMessageBox.warning(self, "Error", "Failed to save image.")
            if file_exists('web/images/changed_clicks',f"screenshot{c1}.png"):
                
                path[self.file] = f'web/images/changed_clicks/screenshot{c1}.png'
                c1+=1
            self.close()


@eel.expose
def snap(file):
    global path
    if __name__ == "__main__":
        app = QApplication(sys.argv)
       
        capturer = Capture(None, file)
        capturer.show()
        app.exec_()
        print(path)
        return path[file]



def replace_mouse_clicks(tasks, path, filename):
    l = list(path.keys())
    for i in range(len(l)):
        for k,v in tasks.items():
            try:
                if isinstance(v[-1][-1],str):
                    if v[-1][-1]==l[i]:
                        tasks[k] = f'web/images/task_clicks/{path[l[i]][36:-4]+filename}.png'
                        copy_file(path[l[i]],f'web/images/task_clicks/{path[l[i]][36:-4]+filename}.png')

                    else:
                        if i==len(l)-1:
                            v[-1] = v[-1][0]
            except:
                continue
    return tasks

keys1 = {}
@eel.expose
def keyboard_text(key, subkey, value, prompt):
    global keys1
    keys1[key] = [subkey, value, prompt]

def change_keyboard_text(tasks, keys1, filename):
   
    for key in list(keys1.keys()):
        for k,v in tasks.items():
            if str(k)==key:
                user_query = keys1[key][2]
                # output = query({"inputs": (user_query), "return_full_text": False, "temperature":0.4})

                # cleaned_response = (output[0]['generated_text']).replace(user_query, "").strip()
                
                tasks[k][keys1[key][0]] = "dynamic"+user_query
               

                copy_file(f"web/images/keyboard_interactions/"+keys1[key][1],f'web/images/task_keyboard/{keys1[key][1][:-3]+filename}.png')
 
    return tasks        



def update_json_file(filename, file_description):
    file_path = "web/tasks.json"
    # Check if the JSON file exists
    if os.path.exists(file_path):
        # Read the existing content
        with open(file_path, 'r') as file:
            data = json.load(file)
    else:
        # Create a new dictionary if the file doesn't exist
        data = {}
    
    # Add or update the filename and description
    data[filename] = file_description
    
    # Write the updated content back to the JSON file
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)
        
    print(f"Updated {file_path} with {filename}: {file_description}")

@eel.expose
def save_recording(filename, description):
    global tasks, path, keys1
    update_json_file(filename, description)
    tasks = replace_mouse_clicks(tasks, path, filename)
    
    tasks = change_keyboard_text(tasks, keys1, filename)
    
    serialize_data(tasks,filename)



q = Queue()
@eel.expose
def record_interactions():
    global tasks, q
    q = Queue()
    delete_files_in_directory('web/images/mouse_clicks')
    delete_files_in_directory('web/images/keyboard_interactions')

    mouse.hook(q.put)       
    
    # Start recording keyboard events
    keyboard.start_recording(recorded_events_queue=q)
    
@eel.expose
def stop_recording():
    global q, tasks
    #keyboard.wait("n+o")   
    mouse.unhook(q.put) 

    # Stop recording keyboard events
    keyboard.stop_recording()

    # Get all events from the queue
    interactions = list(q.queue)
    tasks = separate_tasks(interactions)
   
    for key,value in tasks.items():
        if isinstance(value[0], keyboard._keyboard_event.KeyboardEvent):
            tasks[key] = filter_input(value)
    mouse.unhook_all()
   
    return tasks



@eel.expose
def get_image_files():
    try:
        # List all files in the images directory
        images_dir = 'web/images/mouse_clicks'
        files = os.listdir(images_dir)
        # Filter out non-image files
        image_files = [file for file in files if file.lower().endswith(('jpg', 'jpeg', 'png', 'gif'))]
        
        # Function to extract the numeric part of the filename
        def extract_number(filename):
            match = re.search(r'(\d+)', filename)
            return int(match.group(1)) if match else 0
        
        # Sort files based on the extracted numeric part
        image_files.sort(key=extract_number)
        print(image_files)
        return image_files
    except Exception as e:
        return str(e)

@eel.expose
def get_keyboard_files():
    global tasks
    files = {}
    c = 0
    for key,v in tasks.items():
        try:
            if isinstance(v[0][0],keyboard._keyboard_event.KeyboardEvent):
                for i in range(len(v)):
                    state = False
                    print(v[i])
                    for k in range(len(v[i])):
                        if v[i][k].event_type=="up":
                            c+=1
                            state = True
                    if state:
                        files[key] =  [i, f"screenshot_{c}.png"]

        except:
            pass
    return files

@eel.expose
def get_task_files(folder_path=f"web/tasks/"):
    try:
        # List all files in the given directory
        filenames = os.listdir(folder_path)
        # Filter out only files (not directories)
        filenames = [f for f in filenames if os.path.isfile(os.path.join(folder_path, f))]
        return filenames
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


@eel.expose
def delete_task(file_name):
    # Define the directory path
    directory_path = 'web/tasks/'
    
    # Construct the full file path
    file_path = os.path.join(directory_path, file_name)
    
    try:
        # Check if the file exists
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"File '{file_path}' has been deleted successfully.")
        else:
            print(f"File '{file_path}' does not exist.")
    except Exception as e:
        print(f"An error occurred: {e}")

def load_json(file_path):
    # Load the JSON data from the file as a string
    with open(file_path, "r") as json_file:
        json_string = json_file.read()

    # Parse the JSON string into a dictionary
    data = json.loads(json_string)

    return data

def find_img(value, confidence):
    try:
        time.sleep(2)
        send_button_location = pyautogui.locateOnScreen(value, confidence)
        send_button = pyautogui.center(send_button_location)
        send_button_x, send_button_y = send_button
        pyautogui.click(send_button_x, send_button_y) 
        time.sleep(2)
        return
    except:
        find_img(value, confidence)

@eel.expose
def play_interactions(file):
    file_path = os.path.join(f"web/tasks", f"{file}")
    data = load_json(file_path)
    # for k,v in data.items():
    #     print(k,v)
    time.sleep(3)
    keyboard.press('a')
    
    for key,value in data.items():
        if isinstance(value, str):
            find_img(value, 0.9)
        else:
            for i in value:
                if isinstance(i[0],dict) or (isinstance(i[0],str) and (len(i[0])==1 or i[0]=='\n')):
                    previous_data = []
                    for events in i:
                        try:
                            
                            if events['name']=="left windows" and events['event_type']=='up':
                                if previous_data!=[]:
                                    keyboard.play(previous_data,speed_factor=1.5)
                                    time.sleep(1)
                                pyautogui.press('win')
                            else:
                                previous_data.append(KeyboardEvent(events['event_type'], events['scan_code'], events['name'], events['time'], events['device'], events['modifiers'], events['is_keypad']))
                        except:
                            keyboard.write(events, delay=0.01, restore_state_after=True, exact=None)
                    if previous_data!=[]:
                        keyboard.play(previous_data,speed_factor=1.5)
                        time.sleep(1)
                        
                else:
                    if len(i)==2:
                        mouse.play([WheelEvent(delta=i[0], time=i[1])], speed_factor=1.0)
                        time.sleep(0.1)
                    elif len(i)==3 and isinstance(i[0],str):
                        mouse.play([ButtonEvent(event_type=i[0], button=i[1], time=i[2])], speed_factor=1.0)
                        time.sleep(1.5)
                    elif len(i)==3 and isinstance(i[0],int):
                        mouse.play([MoveEvent(x=i[0], y=i[1], time=i[2])], speed_factor=4.0)
                        time.sleep(0.0001)
                


@eel.expose
def make_fullscreen():
    time.sleep(.1)
    pyautogui.hotkey('win','up')







def llmquery(prompt, text_type):

    url='https://h7nk8a3a20x9yn-11434.proxy.runpod.net/'
    
    client = OpenAI(
                    base_url = url+'v1',
                    api_key='sk-111111111111111111111111111111111111111111111111', 
                )

    query = f"""Based on the prompt - '{prompt}', generate the content for an input field which takes text input whose description is - '{text_type}'. 
    You do not need to genearte full content for the prompt rather what is specifically needed in the input field. The output you will generate will be directly used in the input field. So give the output that I can directly use in the input field. Let's say if the input description is 'email body' write the full email body content only not subject or address or any headline like 'here's your content'.
    e.g. for prompt- 'Write an email to ahmedanwar.aa872@gmail.com about your first anime experience' and input field description- 'email address', the response is 'ahmedanwar.aa872@gmail.com' only nothing more, do not add email subject or body or any title or description or any tag like-(email address). Just the address value.
    for prompt- 'Write an email to ahmedanwar.aa872@gmail.com about your first anime experience' and input field description- 'email subject', the response is 'Sharing My First Anime Experience' only nothing more, do not add email address or body or any title like- 'Email subject:' or description or tag. Just the subject value.
    for prompt- 'Write a facebook post content about my pictures which I took in Japan' and input field description- 'the post body', the response will be- 'Hello friends, so today i am going to show you about the best part of my adventures in Japan.' only nothing more, not any description or any title. Just the post content."""

    response = client.chat.completions.create(
                model="mistral",
                messages=[
                    {"role": "user", "content": query},
                ]
                )
    return response.choices[0].message.content



class ExecuteTask(BaseTool):
    name: str = "Execute tasks"
    description: str = (
        """Executes a task by taking the task name and necessary prompt as the parameter. The task is previously stored in a JSON file.
        
        :param task: str, the name of the task to execute.
        :param prompt: str, the given prompt
        :return: str, a confirmation message indicating the task execution status, e.g., 'done'.
        """
    )

    def _run(self, task: str, prompt: str) -> str:
        info = {}
        file_path = os.path.join(f"web/tasks", f"{task}.json")
        source_folder = "web/tasks"
        destination_folder = "web/temp_tasks"
        source_file_path = os.path.join(source_folder, f"{task}.json")
        destination_file_path = os.path.join(destination_folder, "temp.json")
        shutil.copy(source_file_path, destination_file_path)

        try:
            with open(file_path, "r") as json_file:
                data = json.load(json_file)

            for k, v in data.items():
                if isinstance(v, str):
                    continue
                if isinstance(v[0], str):
                    if v[0].startswith('dynamic'):
                        v[0] = llmquery(prompt,v[0][7:])
                elif isinstance(v[0][0], dict):
                    for i in range(len(v)):
                        if isinstance(v[i][0], str):
                            v[i] = llmquery(prompt, ("".join(v[i][7:])))
                            
            time.sleep(2)
            keyboard.press('a')
            
            for key,value in data.items():
                if isinstance(value, str):
                    find_img(value, 0.9)
                    time.sleep(2)
                else:
                    for i in value:
                        if isinstance(i[0],dict) or (isinstance(i[0],str) and (len(i[0])==1 or i[0]=='\n')):
                            previous_data = []
                            for events in i:
                                try:
                                    
                                    if events['name']=="left windows" and events['event_type']=='up':
                                        if previous_data!=[]:
                                            keyboard.play(previous_data,speed_factor=1.5)
                                            time.sleep(1)
                                        pyautogui.press('win')
                                    else:
                                        previous_data.append(KeyboardEvent(events['event_type'], events['scan_code'], events['name'], events['time'], events['device'], events['modifiers'], events['is_keypad']))
                                except:
                                    keyboard.write(events, delay=0.01, restore_state_after=True, exact=None)
                            if previous_data!=[]:
                                keyboard.play(previous_data,speed_factor=1.5)
                                time.sleep(1)
                                
                        else:
                            if len(i)==2:
                                mouse.play([WheelEvent(delta=i[0], time=i[1])], speed_factor=1.0)
                                time.sleep(0.1)
                            elif len(i)==3 and isinstance(i[0],str):
                                mouse.play([ButtonEvent(event_type=i[0], button=i[1], time=i[2])], speed_factor=1.0)
                                time.sleep(1.5)
                            elif len(i)==3 and isinstance(i[0],int):
                                mouse.play([MoveEvent(x=i[0], y=i[1], time=i[2])], speed_factor=4.0)
                                time.sleep(0.0001)
            return 'done'


        except Exception as e:
            return {"error": str(e), "message": "Failed to read the JSON file."}


@eel.expose
def agent_on_call(prompt):

    execute_tasks = ExecuteTask()

    task_coordinator = Agent(role = "Task Coordinator",
                        goal = """Select the most suitable task from all the tasks information and send the task name to Task Executor. For example if the task information is '{'linkedin_post': 'This task allows to post on linkedin as the user requires', 'instagram_post': 'This task allows to post on instagram as the user requires'}' when the user wants you to post on instagram you return instagram_post.""",
                        backstory = """You are an extremely experienced task coordinator in a company that does automation task based on user needs. 
                        You will be provided the information of all available tasks and their corresponding descriptions. 
                        You always analyze the job assigned in depth and decide what type of task it actually requires from the task list. 
                        You are absolutely a professional who on the basis of a given command can understand and choose what type of task the job requires and return the task name only. 
                        Your sole purpose is to return the decided task from the task list.
                        You never suggest your own tasks rather choose task from the given tasks list only. Also you never generate any content, only select the required task.""",
                        allow_delegation = False,
                        verbose = True,
                        )

    task_executor = Agent(role = "Task Executor",
                      goal = """Execute the task using the tool provided after taking the task name from Task Coordinator and receiving necessary prompt. Do not change the task name provided by task Coordinator.""",
                      backstory = """You are an extremely experienced Task Executor working in a leading think tank. 
                      Your company has provided you with a special tool named 'execute_tasks' to execute specific tasks. .
                      You get a prompt and Task Coordinator gives you a task name and you utilize these two to execute the task using the tool provided.
                      Your sole purpose is to execute the task using the tool provided. You never create any content or modify any input anything just execute what you were asked to. 
                      """, 
                      allow_delegation = False,
                      verbose = True,
                      tools=[execute_tasks], 
                      )


    with open('web/tasks.json', 'r') as file:
        tasks_info = json.load(file)
    
    task1 = Task (description="Select the task based on the prompt- "+prompt+ "and all the task description from- "+str(tasks_info)+"send it to the Task Executor",
                agent = task_coordinator,
                expected_output="The required task name only according to the job assigned and no other content")
    
    
    task2 = Task (description= f"""Execute the task whose name was provided by Task Coordinator and use the prompt- {prompt} while using the tool. 
                  Make sure to pass the exact task name as input for the tool that was provided by the task coordinator. Don't use your own assumed task name rather use the one provided by the Task Coordinator.
                  And never change the prompt.""",
                agent = task_executor,
                expected_output="The required task gets executed using the task name provided by Task Coordinator.")
    

    crew = Crew(
                agents=[task_coordinator, task_executor],
                tasks=[task1, task2],
                process=Process.sequential,
                verbose=2
            )

    result = crew.kickoff()

    print(result)






eel.start('home.html')

