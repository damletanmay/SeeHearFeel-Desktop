# %%
import re
import os
import sys
import nltk
import shutil
import platform
import threading
import subprocess
import tkinter as tk
from CTkListbox import *
from customtkinter import *
from moviepy.editor import *
from tkinter import StringVar
from tkinter import filedialog
from tkinter import messagebox
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from moviepy.video.fx.resize import resize

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')

# %%
# this method is to get resource path when using assets for software
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

#  Some essential public variables
cwd = os.getcwd()
os_name = platform.system().lower()
assets_file_path = os.path.join(cwd,"assets")

assets_file_path = resource_path(assets_file_path)
movie_paths = resource_path(os.path.join(cwd,"movie_paths.txt"))

if not os.path.exists(movie_paths):
    fp = open(movie_paths,'x')
    fp.close()

# %%
# this function uses 
def clean_text(text):
    #tokenizing the sentence
    text.lower()
    #tokenizing the sentence
    words = word_tokenize(text)
    
    tagged = nltk.pos_tag(words)
    tense = {}
    tense["future"] = len([word for word in tagged if word[1] == "MD"])
    tense["present"] = len([word for word in tagged if word[1] in ["VBP", "VBZ","VBG"]])
    tense["past"] = len([word for word in tagged if word[1] in ["VBD", "VBN"]])
    tense["present_continuous"] = len([word for word in tagged if word[1] in ["VBG"]])

    #stopwords that will be removed
    # stop_words = set(["I'm","mightn't", 're', 'wasn', 'wouldn', 'be', 'has', 'that', 'does', 'shouldn', 'do', "you've",'off', 'for', "didn't", 'm', 'ain', 'haven', "weren't", 'are', "she's", "wasn't", 'its', "haven't", "wouldn't", 'don', 'weren', 's', "you'd", "don't", 'doesn', "hadn't", 'is', 'was', "that'll", "should've", 'a', 'then', 'the', 'mustn', 'i', 'nor', 'as', "it's", "needn't", 'd', 'am', 'have',  'hasn', 'o', "aren't", "you'll", "couldn't", "you're", "mustn't", 'didn', "doesn't", 'll', 'an', 'hadn', 'whom', 'y', "hasn't", 'itself', 'couldn', 'needn', "shan't", 'isn', 'been', 'such', 'shan', "shouldn't", 'aren', 'being', 'were', 'did', 'ma', 't', 'having', 'mightn', 've', "isn't", "won't"])
    stop_words = [
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", 
        "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", "they", "them", "their", 
        "theirs", "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are", "was", 
        "were", "be", "been", "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", "the", "and", 
        "but", "if", "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", 
        "into", "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", "on", "off", 
        "over", "under", "again", "further", "then", "once", "here", "there", "when", "where", "why", "how", "all", "any", 
        "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so", 
        "than", "too", "very", "s", "t", "can", "will", "just", "don", "should", "now"
    ]

    #removing stopwords and applying lemmatizing nlp process to words
    lr = WordNetLemmatizer()
    filtered_text = []
    for w,p in zip(words,tagged):
        if w not in stop_words:
            if p[1]=='VBG' or p[1]=='VBD' or p[1]=='VBZ' or p[1]=='VBN' or p[1]=='NN':
                filtered_text.append(lr.lemmatize(w,pos='v'))
            elif p[1]=='JJ' or p[1]=='JJR' or p[1]=='JJS'or p[1]=='RBR' or p[1]=='RBS':
                filtered_text.append(lr.lemmatize(w,pos='a'))

            else:
                filtered_text.append(lr.lemmatize(w))

    #adding the specific word to specify tense
    words = filtered_text
    temp=[]
    for w in words:
        if w=='I':
            temp.append('Me')
        else:
            temp.append(w)
    words = temp
    probable_tense = max(tense,key=tense.get)

    if probable_tense == "past" and tense["past"]>=1:
        temp = ["Before"]
        temp = temp + words
        words = temp
    elif probable_tense == "future" and tense["future"]>=1:
        if "Will" not in words:
                temp = ["Will"]
                temp = temp + words
                words = temp
        else:
            pass
    elif probable_tense == "present":
        if tense["present_continuous"]>=1:
            temp = ["Now"]
            temp = temp + words
            words = temp
    return words

# %%
# extract text from vtt or srt files
def extract_text(srt_file_path):
    subtitles = []
    with open(resource_path(srt_file_path), 'r', encoding='utf-8') as file:
        lines = file.readlines()
        sub = None
        for line in lines:
            line = line.strip()
            if line.isdigit():
                if sub:
                    subtitles.append(sub)
                sub = {'index': int(line), 'text': ''}
            elif '-->' in line:
                pass  # Skip time stamps
            elif line:  # Non-empty line assumed to be subtitle text
                if sub:
                    sub['text'] += line + ' '
        if sub:  # Append the last subtitle if it exists
            subtitles.append(sub)

    sub_all = ""

    for sub in subtitles:
        sub_all+=sub['text'].strip() + " "

    sub_all = re.sub(r'[^A-Za-z0-9\s ]', '', sub_all) # replace everything except space
    
    return sub_all

# %%
# List all files in the directory
def list_files_in_directory(directory_path):
    files = os.listdir(resource_path(directory_path))
    
    # Convert each file name to string format
    files_string_format = [str(file).lower() for file in files]
    
    return files_string_format

# %%
# get movie order of sign language
def make_video_order(words):
    assets = list_files_in_directory(assets_file_path) # get all assets
    
    video_order = []
    for word in words:
        if word.lower() +".mp4" not in assets:
            for w in word:
                video_order.append(w+".mp4")
        else:
            video_order.append(word+".mp4")
    return video_order

# %%
def swap_commentary(video_clip,commentary_file,destination_path):
    
    # Load the new audio file

    audio_clip = AudioFileClip(resource_path(commentary_file))
    audio_clip.duration = video_clip.duration 
    # Replace the audio of the video clip with the new audio clip
    video_clip = video_clip.set_audio(audio_clip)

    # Write the modified video with the replaced audio to a new file
    video_clip.write_videofile(destination_path,threads = os.cpu_count(),verbose=False,logger=None)

    # Close the clips
    video_clip.close()
    audio_clip.close()

# %%
# make movie
def make_movie(video_order,og_video_file_path,audio_commentary_file_path,destination_path):

    sign_language_video = VideoFileClip(resource_path(os.path.join(assets_file_path,video_order[0].lower().capitalize())))
    
    og_video = VideoFileClip(og_video_file_path)
    
    for i in video_order[1:]:
        try:
            video_clip = VideoFileClip(resource_path(os.path.join(assets_file_path,i.lower().capitalize())))
            sign_language_video = concatenate_videoclips([sign_language_video,video_clip])
            # setting.exe
            if(round(sign_language_video.duration) >= round(og_video.duration)):
                sign_language_video.duration = og_video.duration # set same duration
                break
            
        except Exception as e:
            print(e)
            print("Error in File "+i)
            return False,None

    # Resize the sign language video to 30% of its original size
    sign_language_video = resize(sign_language_video,width=og_video.w // 3)
    
    # Create a composite video with main video on the left and sign language video on the bottom right
    # sign_language_video = clips_array([[og_video, sign_language_video.set_position(("right", "bottom"))]])
    
    sign_language_video = CompositeVideoClip([og_video.set_duration(sign_language_video.duration), sign_language_video.set_position(("right", "bottom"))])

    # write integrated video to destination video
    destination_path_video = os.path.join(destination_path, "movie" + og_video_file_path[-4:])
    
    swap_commentary(sign_language_video,audio_commentary_file_path,destination_path_video)

    return True


# %%
# To open File Explorer
def open_file_explorer(path):
    if os_name == 'windows':
        os.startfile(os.path.abspath(path))
    else:
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.call([opener, path])
    

# To add movie path to each file
def add_movie_path(filename, path):
    with open(filename, 'a') as file:
        file.write('\n' + path)

def load_movie_paths(filename):
    unique_paths = set()  # Use a set to eliminate duplicates
    
    # read files that exists
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            for line in file:
                path = line.strip()
                if os.path.exists(path):
                    unique_paths.add(path)
    
    # replace data in file with only exisiting files, delete other data
    if os.path.exists(filename):
        with open(filename, 'w') as file:
            for i in list(unique_paths):
                file.write('\n' + i)

    return list(unique_paths)  # Convert set back to a list

# %%
def format_destination(directory_path):

    # delete all folders inside directory path
    all_sub_folders = [x[0] for x in os.walk(directory_path)]
    
    # remove all folders
    if len(all_sub_folders) != 0:
        for i in all_sub_folders[1:]:
            if os.path.exists(i):
                shutil.rmtree(i)

    # Get list of all files in the directory
    files = os.listdir(directory_path)
    if len(files) != 0:
        # Iterate over each file and delete it
        for file in files:
            file_path = os.path.join(directory_path, file)
            os.remove(file_path)

# %%
class VideoUploader:
    
    def __init__(self, root, default_font,title_font):
        # creating a notebook
        self.root = root
        root.title("See Hear Feel")
        self.tabView = CTkTabview(master = root,width=800, height=500, border_width = 0, segmented_button_fg_color = "black", segmented_button_selected_color= "#1F538D", fg_color="#1A1A1A",bg_color="#1A1A1A")
        self.tabView.pack(fill='both', expand=True)

        # add tabs
        self.tabView.add("Create Movie") 
        self.tabView.add("Library")
        self.tabView.set("Create Movie") # pre select first window

        for button in self.tabView._segmented_button._buttons_dict.values():
            button.configure(width=100, height=50,font = default_font)
        
        # creating a Frame to contain all create movie elements
        self.create_movie_frame = self.tabView.tab("Create Movie")

        # title
        self.title_label = CTkLabel(master = self.create_movie_frame, text="SeeHearFeel", font = title_font, text_color="white")
        self.title_label.pack(padx=10, pady=10)
        
        # Instructions
        self.instructions_text = StringVar()
        self.instructions_text.set("Enter all required files to create the Movie")
        self.text = CTkLabel(master = self.create_movie_frame, font = default_font, textvariable = self.instructions_text)
        self.text.pack(pady=10)
        
        # Progress Bar
        self.progress = CTkProgressBar(master = self.create_movie_frame, height = 20, width = 500, mode = "determinate")
        self.progress.set(0)
        self.progress.pack(pady=10)

        # Select Movie button
        self.movie_button = CTkButton(master=self.create_movie_frame, text="Select Movie", command=lambda: self.upload_file("movie"), width=30)
        self.movie_button.pack(pady=10)

        # Select Subtitles button
        self.subtitles_button = CTkButton(master=self.create_movie_frame, text="Select Subtitles", command=lambda: self.upload_file("subtitles"), width=30)
        self.subtitles_button.pack(pady=10)
    
        # Select Audio Commentary button 
        self.commentary_button = CTkButton(master=self.create_movie_frame, text="Select Audio Commentary", command=lambda: self.upload_file("commentary"), width=30)
        self.commentary_button.pack(pady=10)

        # Select Folder button
        self.destination_button = CTkButton(master=self.create_movie_frame, text="Select Destination Folder", command=lambda: self.upload_file("folder"), width=30)
        self.destination_button.pack(pady=10)
        
        # create movie button
        self.create_movie_button = CTkButton(self.create_movie_frame, text="Create Movie", command = threading.Thread(target = self.display_textbox).start, width=20)
        self.create_movie_button.configure(state=tk.DISABLED)
        self.create_movie_button.pack(pady=10)
        
        # dictionary to hold paths
        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}

        # create library page
        self.library_tab_frame = self.tabView.tab("Library")
        self.processed_movies_path = load_movie_paths(movie_paths) # get all movie paths

        # a text box 
        self.ifFilesExist = StringVar()
        self.ifFilesExist.set("Double Click a Folder to open it")
        self.library_text_box = CTkLabel(master = self.library_tab_frame, textvariable=self.ifFilesExist)
        self.library_text_box.pack(padx=10, pady=10)

        if len(self.processed_movies_path) == 0:
            # If Libary is empty change text
            self.ifFilesExist.set("Library is empty!")

        # self.listbox = tk.Listbox(self.library_tab_frame, yscrollcommand=self.scrollbar.set, selectmode=tk.SINGLE)
            
        # self.listbox.pack(side="right", fill="both", expand=True)

        self.scrollbar = CTkScrollbar(master=self.library_tab_frame)
        self.scrollbar.pack(side = "right", fill = "y")

        # Text box
        self.library_files_list_box = tk.Listbox(self.library_tab_frame, yscrollcommand=self.scrollbar.set, selectmode=tk.SINGLE)
        self.library_files_list_box.config(bg="#1A1A1A",fg="white",selectforeground="white",selectbackground="#1F538D")

        if len(self.processed_movies_path) != 0:
            for path in self.processed_movies_path:
                self.library_files_list_box.insert(tk.END, path)

        self.library_files_list_box.bind("<Double 1>", self.on_select)
        
        self.scrollbar.configure(command=self.library_files_list_box.yview)

        self.library_files_list_box.pack(padx=10, pady=10, fill="both", expand=True)

        # is Movie Processing
        self.isMovieProcessing = False

    # on double click of a movie path, handle the opening of a file explorer despite the system
    def on_select(self,event):
        selected_index = self.library_files_list_box.curselection()
        print(selected_index)
        if selected_index:
            selected_path = self.library_files_list_box.get(selected_index[0])
            open_file_explorer(selected_path)
          
    # change the create movie button whenever each file is updated
    def change_create_movie_button(self):
        # if all files are uploaded, disable the button else keep it normal
        if (self.uploaded_files["movie"] is not None) and (self.uploaded_files["subtitles"] is not None) and (self.uploaded_files["commentary"] is not None) and (self.uploaded_files["folder"] is not None):
            self.create_movie_button.configure(state=tk.NORMAL)
        else:
            self.create_movie_button.configure(state=tk.DISABLED)
                
    def recreate_create_movie_button(self,createNormal):
        self.create_movie_button.destroy()
        self.create_movie_button = CTkButton(self.create_movie_frame, text="Create Movie", command = threading.Thread(target = self.display_textbox).start, width=20)
        if createNormal:
            self.create_movie_button.configure(state=tk.NORMAL)
        else:
            self.create_movie_button.configure(state=tk.DISABLED)
        self.create_movie_button.pack(pady=10)

    # display alert 
    def display_textbox(self):
        choice = messagebox.askyesno("Alert", "The {} folder will be completely erased and Movie will be created, Click Yes to continue".format(self.uploaded_files["folder"]))
         # when user clicks yes create 
        if choice:
            # try to create a movie
            try:
                self.create_movie()
            except Exception as e:
                print(e)
                self.reset_everything() # reset everything if some error occurs 
                messagebox.showinfo("Alert!","Movie creation failed")
        else:
            # if choice is no
            self.recreate_create_movie_button(True)


    # upload file paths to uploaded_files variable
    def upload_file(self, file_type):
        if not self.isMovieProcessing:                
            if file_type == "movie":
                try:
                    self.uploaded_files["movie"] = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi")])
                    if os.path.exists(self.uploaded_files["movie"]):      
                        self.movie_button.configure(text=self.uploaded_files["movie"][self.uploaded_files["movie"].rfind('/')+1:])
                        self.change_create_movie_button()
                    else:
                        raise Exception("Movie Error")
                except Exception as e:
                    print(e)
                    self.uploaded_files["movie"] = None
                    self.movie_button.configure(text="Select Movie")
                    self.recreate_create_movie_button(False)
                    self.change_create_movie_button()

            if file_type == "subtitles":
                try: 
                    self.uploaded_files["subtitles"] = filedialog.askopenfilename(filetypes=[("Subtitle Files", "*.srt *.vtt")])
                    if os.path.exists(self.uploaded_files["subtitles"]):           
                        self.subtitles_button.configure(text=self.uploaded_files["subtitles"][self.uploaded_files["subtitles"].rfind('/')+1:])
                        self.change_create_movie_button()
                    else:
                        raise Exception("Subtitles Error")
                except Exception as e:
                    print(e)
                    self.uploaded_files["subtitles"] = None
                    self.subtitles_button.configure(text="Select Subtitles")
                    self.recreate_create_movie_button(False)
                    self.change_create_movie_button()

            if file_type == "commentary":
                try:
                    self.uploaded_files["commentary"] = filedialog.askopenfilename(filetypes=[("MP3 Files", "*.mp3")])
                    if os.path.exists(self.uploaded_files["commentary"]):           
                        self.commentary_button.configure(text=self.uploaded_files["commentary"][self.uploaded_files["commentary"].rfind('/')+1:])
                        self.change_create_movie_button()
                    else:
                        raise Exception("Commentary Error")
                    
                except Exception as e:
                    print(e)
                    self.uploaded_files["commentary"] = None
                    self.commentary_button.configure(text="Select Audio Commentary")
                    self.recreate_create_movie_button(False)
                    self.change_create_movie_button()

            if file_type == "folder":
                try:
                    self.uploaded_files["folder"] = filedialog.askdirectory(title="Select Folder")
            
                    if os.path.exists(self.uploaded_files["folder"]):    
                        self.destination_button.configure(text=self.uploaded_files["folder"][self.uploaded_files["folder"].rfind('/')+1:])
                        self.change_create_movie_button()
                    else:
                      raise Exception("Folder Error")
                    
                except Exception as e:
                    print(e)
                    self.uploaded_files["folder"] = None
                    self.destination_button.configure(text="Select Destination Folder")
                    self.recreate_create_movie_button(False)
                    self.change_create_movie_button()

    # reset buttons once process is over
    def reset_everything (self):
        # reset everything 
        self.uploaded_files = {"movie": None, "subtitles": None, "commentary": None,"folder":None}
        
        self.movie_button.configure(text="Select Movie")
        self.subtitles_button.configure(text="Select Subtitles")
        self.commentary_button.configure(text="Select Audio Commentary")
        self.destination_button.configure(text="Select Destination Folder")
        
        # update create button by destroying it and creating a new one in it's place
        self.recreate_create_movie_button(False)
        
        self.progress.set(0)
        self.instructions_text.set("Enter all required files to create the Movie")
        self.isMovieProcessing = False
        
        # update list box by redifining it 
        self.library_files_list_box.delete(0,tk.END)
        self.processed_movies_path = load_movie_paths(movie_paths) # get all movie paths
        for path in self.processed_movies_path:
            self.library_files_list_box.insert(tk.END, path)

        self.library_files_list_box.update()

        if len(self.processed_movies_path)!=0:
            self.ifFilesExist.set("Double Click a Folder to open it")
    
    def create_movie(self):
        
        self.progress.set(0)
        self.root.update_idletasks() 
        self.instructions_text.set("Creating Movie Please Wait...")

        self.isMovieProcessing = True
        self.recreate_create_movie_button(False)
        
        self.progress.set(0.1)
        self.instructions_text.set("Formating Destination...")

        format_destination(self.uploaded_files["folder"]) # format destination folder
        
        # extract text from subtitles
        subtitles = extract_text(self.uploaded_files["subtitles"])
        
        # get words inside subtitles
        words = clean_text(subtitles) # get all the words     

        # get video order 
        video_order = make_video_order(words)

        self.progress.set(0.45)
        self.instructions_text.set("Processing Movie...")

        isMovieDone = make_movie(video_order, self.uploaded_files["movie"],self.uploaded_files["commentary"], self.uploaded_files["folder"]) # make sign language video
        
        self.progress.set(0.75)
        self.instructions_text.set("Saving Movie...")

        if isMovieDone:
            
            add_movie_path(movie_paths,self.uploaded_files["folder"]) # add movie path, when movie is done

            # copy subtitles
            subtitles_destination = self.uploaded_files["folder"]
            subtitles_destination = os.path.join(self.uploaded_files["folder"],"movie"+ self.uploaded_files["subtitles"][-4:])
            shutil.copy(self.uploaded_files["subtitles"],subtitles_destination) # copy subtitles
            
            self.progress.set(1)
            self.instructions_text.set("Movie Finished")

            # display message
            messagebox.showinfo("Movie Successfully Created!","Movie created in folder {}".format(self.uploaded_files["folder"]))

            self.reset_everything()
        else:
            self.reset_everything()
            messagebox.showinfo("Alert!","Movie creation failed")

# %%
if __name__ == "__main__":
   
    See_Hear_Feel_App = CTk() # making a custom Tkinter app
    See_Hear_Feel_App.resizable(width=False,height=False) 
    set_appearance_mode("dark")
    set_default_color_theme("dark-blue")
    default_font = CTkFont(family="Aptos", size=16)
    title_font = CTkFont(family="Aptos", size=26)
    uploader = VideoUploader(See_Hear_Feel_App,default_font,title_font)
    See_Hear_Feel_App.mainloop()


