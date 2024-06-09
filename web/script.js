document.getElementById('add-task').style.display = 'none';
document.getElementById('task-list').style.display = 'none';
document.getElementById('import-export').style.display = 'none';
document.getElementById('perform-task').style.display = 'block';

eel.make_fullscreen()();

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.getElementById('main-content');
    
    if (sidebar.style.left === '0px' || sidebar.style.left === '') {
        sidebar.style.left = '-250px';
        mainContent.style.marginLeft = '0px';
    } else {
        sidebar.style.left = '0px';
        mainContent.style.marginLeft = '250px';
    }
}

async function showSection(sectionId) {
    document.getElementById('add-task').style.display = 'none';
    document.getElementById('task-list').style.display = 'none';
    document.getElementById('import-export').style.display = 'none';
    document.getElementById('perform-task').style.display = 'none';
    document.getElementById('recording-controls').style.display = 'none'; 
    document.getElementById('edit-task').style.display = 'none';

    //add-task page
    document.getElementById('recording-message').classList.add('hidden');
    document.getElementById('stop-recording').classList.add('hidden');
    document.getElementById('recording-controls').classList.add('hidden');
    document.getElementById('recording-message').textContent = 'Recording!';
    
    document.getElementById(sectionId).style.display = 'block';

    if (sectionId === 'edit-task') {
        try {
            // Fetch the list of image files for mouse clicks and keyboard interactions from the Python backend
            const mouseClickFiles = await eel.get_image_files()();
            const keyboardInteractionFiles = await eel.get_keyboard_files()();

            // Get the containers for displaying the images
            const mouseClicksContainer = document.getElementById('mouse-clicks');
            const keyboardInteractionsContainer = document.getElementById('keyboard-interactions');
            console.log(mouseClickFiles);
            console.log(keyboardInteractionFiles);
            // Clear any existing images before appending new ones
            mouseClicksContainer.innerHTML = '';
            keyboardInteractionsContainer.innerHTML = '';

            // Function to create image elements and append to the container
            function appendImages(container, files) {
                files.forEach(filename => {
                    const div = document.createElement('div');
                    const img = document.createElement('img');
                    img.src = `images/mouse_clicks/${filename}`;
                    const button = document.createElement('button');
                    button.textContent = 'Change';
                    button.classList.add('btn-black');
                    const button2 = document.createElement('button');
                    button2.textContent = 'View';
                    button2.classList.add('btn-black');
                    button.onclick = () => {
                        // Open the image in full screen
                        openImageFullScreen(img, filename, container, true);
                        
                    };
                    button2.onclick = () => {
                        // Open the image in full screen
                        openImageFullScreen(img, filename, container, false);
                        
                    };
                    div.appendChild(img);
                    div.appendChild(button);
                    div.appendChild(button2);
                    container.appendChild(div);
                });
            }
            
            function openImageFullScreen(img, filename, container, value) {
                // Create a new fullscreen div
                const fullscreenDiv = document.createElement('div');
                fullscreenDiv.style.position = 'fixed';
                fullscreenDiv.style.top = '0';
                fullscreenDiv.style.left = '0';
                fullscreenDiv.style.width = '100vw';
                fullscreenDiv.style.height = '100vh';
                fullscreenDiv.style.backgroundImage = `url(${img.src})`;
                fullscreenDiv.style.backgroundSize = 'contain';
                fullscreenDiv.style.backgroundRepeat = 'no-repeat';
                fullscreenDiv.style.zIndex = '1000';
              
                // Add the fullscreen div to the body
                document.body.appendChild(fullscreenDiv);
              
                // Request fullscreen mode
                fullscreenDiv.requestFullscreen();

                // Add an event listener for fullscreen change
                fullscreenDiv.addEventListener('fullscreenchange', async () => {
                    if (document.fullscreenElement && container!=keyboardInteractionsContainer && value==true) {
                        // When the fullscreen is entered, call the Python function via eel
                        var src2 = await eel.snap(filename)();
                        console.log(src2);
                        img.src = `images/changed_clicks/${src2.slice(26)}`;
                    }
                });
              
                // Add an event listener to exit fullscreen mode when the div is clicked
                fullscreenDiv.addEventListener('click', () => {
                  document.exitFullscreen();
                  document.body.removeChild(fullscreenDiv);
                });
              }
            function appendKImages(container, data){
                for (const key in data) {
                    if (data.hasOwnProperty(key)) {
                        const value = data[key][1];
                        const subkey = data[key][0];
                        
                        // button.onclick = () => sendKey(key);

                        const div = document.createElement('div');
                        const img = document.createElement('img');
                        img.src = `images/keyboard_interactions/${value}`;
                        const button = document.createElement('button');
                        button.textContent = 'Make it Dynamic';
                        button.classList.add('btn-black');
                        const button2 = document.createElement('button');
                        button2.textContent = 'View';
                        button2.classList.add('btn-black');
                        button2.onclick = () => {
                            // Open the image in full screen
                            openImageFullScreen(img, value, container, false);
                            
                        };
                        button.onclick = () => {
                            const textBox = document.createElement('input');
                            textBox.type = 'text';
                            textBox.placeholder = 'Enter the content description here';
                            
                            const saveButton = document.createElement('button');
                            saveButton.textContent = 'Save';
                            saveButton.classList.add('btn-black');
                            saveButton.onclick = () => {
                                // Call the eel function
                                eel.keyboard_text(key, subkey ,value, textBox.value)();
                                
                                textBox.style.display="none";
                                saveButton.style.display="none";
                            };
                            
                            // Append the text box and Save button to the div
                            div.appendChild(textBox);
                            div.appendChild(saveButton);
                            
                            
                            
                        };
                        div.appendChild(img);
                        div.appendChild(button2);
                        div.appendChild(button);
                        container.appendChild(div);
                    }
                }
            }

            // Append images to respective containers
            appendImages(mouseClicksContainer, mouseClickFiles);
            appendKImages(keyboardInteractionsContainer, keyboardInteractionFiles);

        } catch (error) {
            console.error('Error fetching images:', error);
        }
    }
    else if(sectionId === 'task-list'){
        const taskfiles = await eel.get_task_files()();
        // Get the containers for displaying the tasks
        const taskContainer = document.getElementById('task-list-tasks');
        taskContainer.innerHTML = '';
        // Function to create image elements and append to the container
        function appendTasks(container, files) {
            files.forEach(filename => {
                const div = document.createElement('div');
                const task = document.createElement('div');
                task.innerHTML = `${filename}`;
               

                const button = document.createElement('button');
                button.textContent = 'Play';
                button.classList.add('btn-black');

                const deletet = document.createElement('button');
                deletet.textContent = 'Delete';
                deletet.classList.add('btn-black');


                button.onclick = () => {
                    eel.play_interactions(filename)();
                };

                deletet.onclick = () => {
                    eel.delete_task(filename)().then(() => {
                        container.removeChild(div);
                    }).catch(error => {
                        console.error('Error deleting task:', error);
                    });
                };

                div.appendChild(task);
                div.appendChild(button);
                div.appendChild(deletet);
                container.appendChild(div);
            });
        }

        // Append tasks to respective containers
        appendTasks(taskContainer, taskfiles);

    }
}

function startRecording() {
    document.getElementById('recording-message').classList.remove('hidden');
    document.getElementById('stop-recording').classList.remove('hidden');
    document.getElementById('recording-controls').classList.remove('hidden');
    document.getElementById('recording-controls').style.display = 'block';

    eel.record_interactions()()
}

function stopRecording() {
    document.getElementById('recording-message').textContent = 'Recorded Task!';
    document.getElementById('stop-recording').style.display = 'none';
    eel.stop_recording()()
}

function saveRecording() {
    var filename = document.getElementById('task_name').value;
    var file_description = document.getElementById('task_description').value;
    eel.save_recording(filename, file_description)()
    showSection('perform-task');
    document.getElementById('recording-message').classList.add('hidden');
    document.getElementById('stop-recording').classList.add('hidden');
    document.getElementById('recording-controls').classList.add('hidden');
    document.getElementById('recording-controls').style.display = 'none';
    document.getElementById('recording-message').textContent = 'Recording!';
}

function cancelRecording() {
    showSection('perform-task');
    document.getElementById('recording-message').classList.add('hidden');
    document.getElementById('stop-recording').classList.add('hidden');
    document.getElementById('recording-controls').classList.add('hidden');
    document.getElementById('recording-controls').style.display = 'none';
    document.getElementById('recording-message').textContent = 'Recording!';
}

function cancelEdit() {
    document.getElementById('add-task').style.display = 'block';
    document.getElementById('task-list').style.display = 'none';
    document.getElementById('import-export').style.display = 'none';
    document.getElementById('perform-task').style.display = 'none';
    document.getElementById('recording-controls').style.display = 'block'; 
    document.getElementById('edit-task').style.display = 'none';
    document.getElementById('recording-message').style.display = 'block';
    
    document.getElementById('recording-message').textContent = 'Recorded! Save now?';
}

function saveEdit() {
    const selectedMouseClicks = Array.from(document.querySelectorAll('#mouse-clicks img')).map(img => img.src);
    const selectedKeyboardInteractions = Array.from(document.querySelectorAll('#keyboard-interactions img')).map(img => img.src);
    
    
    document.getElementById('add-task').style.display = 'block';
    document.getElementById('task-list').style.display = 'none';
    document.getElementById('import-export').style.display = 'none';
    document.getElementById('perform-task').style.display = 'none';
    document.getElementById('recording-controls').style.display = 'block'; 
    document.getElementById('edit-task').style.display = 'none';
    document.getElementById('recording-message').style.display = 'block';
    
    document.getElementById('recording-message').textContent = 'Recorded! Save now?';
}

function sendPrompt() {
    // Change the image source
    
    const userPrompt = document.getElementById('user-prompt').value;
    document.getElementById('perform').src = 'images/owngpt.gif';
    if (userPrompt.trim() !== '') {
        alert('Prompt sent: ' + userPrompt);
        eel.agent_on_call(userPrompt)();
        // Add your logic to handle the prompt here
    } else {
        alert('Please enter a prompt.');
    }
}

// Initially show the Perform Task section
document.addEventListener('DOMContentLoaded', () => {
    showSection('perform-task');
});
