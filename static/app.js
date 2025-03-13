// DOM Elements
const newQuestBtn = document.getElementById('new-quest-btn');
const questFormContainer = document.getElementById('quest-form-container');
const questForm = document.getElementById('quest-form');
const cancelBtn = document.getElementById('cancel-btn');
const activeQuestsContainer = document.getElementById('active-quests');
const completedQuestsContainer = document.getElementById('completed-quests');
const completedQuestsColumn = document.getElementById('completed-quests-column');
const showCompletedCheckbox = document.getElementById('show-completed');
const questCardTemplate = document.getElementById('quest-card-template');
const themeToggle = document.getElementById('theme-toggle');

// API URL - Change this to match your deployed backend URL
// For local development
let API_URL = '/api/quests';
// For production
// const API_URL = 'https://your-deployed-app.onrender.com/api/quests';

// Theme functionality
function loadTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
}

function updateThemeIcon(theme) {
    const icon = themeToggle.querySelector('i');
    if (theme === 'dark') {
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    } else {
        icon.classList.remove('fa-sun');
        icon.classList.add('fa-moon');
    }
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadQuests();
    loadTheme();
    // Ensure form is hidden by default
    questFormContainer.classList.add('hidden');
});

newQuestBtn.addEventListener('click', showQuestForm);
cancelBtn.addEventListener('click', hideQuestForm);
questForm.addEventListener('submit', handleFormSubmit);
showCompletedCheckbox.addEventListener('change', toggleCompletedQuests);
themeToggle.addEventListener('click', toggleTheme);

// Functions
async function loadQuests() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) throw new Error('Failed to fetch quests');
        
        const quests = await response.json();
        
        // Clear containers
        activeQuestsContainer.innerHTML = '';
        completedQuestsContainer.innerHTML = '';
        
        // Render quests
        quests.forEach(quest => {
            const questElement = createQuestElement(quest);
            if (quest.completed) {
                completedQuestsContainer.appendChild(questElement);
            } else {
                activeQuestsContainer.appendChild(questElement);
            }
        });
        
        // Show/hide the completed quests column based on checkbox
        toggleCompletedQuests();
    } catch (error) {
        console.error('Error loading quests:', error);
        alert('Failed to load quests. Please try again later.');
    }
}

function createQuestElement(quest) {
    // Clone template
    const questElement = questCardTemplate.content.cloneNode(true).querySelector('.quest-card');
    
    // Set quest data
    questElement.dataset.id = quest.id;
    questElement.dataset.type = quest.quest_type;
    
    questElement.querySelector('.quest-title').textContent = quest.title;
    questElement.querySelector('.quest-type').textContent = quest.quest_type;
    questElement.querySelector('.quest-description').textContent = quest.description;
    questElement.querySelector('.quest-reward').textContent = quest.reward;
    questElement.querySelector('.quest-creator').textContent = quest.creator;
    
    // Set up buttons
    const completeBtn = questElement.querySelector('.complete-btn');
    const deleteBtn = questElement.querySelector('.delete-btn');
    
    if (quest.completed) {
        completeBtn.innerHTML = '<i class="fas fa-undo"></i> Reactivate';
    } else {
        completeBtn.innerHTML = '<i class="fas fa-check"></i> Complete';
    }
    
    completeBtn.addEventListener('click', () => toggleQuestCompletion(quest.id, !quest.completed));
    deleteBtn.addEventListener('click', () => deleteQuest(quest.id));
    
    return questElement;
}

function showQuestForm() {
    questFormContainer.classList.remove('hidden');
    questForm.reset();
}

function hideQuestForm() {
    questFormContainer.classList.add('hidden');
}

function toggleCompletedQuests() {
    if (showCompletedCheckbox.checked) {
        completedQuestsColumn.classList.remove('hidden');
    } else {
        completedQuestsColumn.classList.add('hidden');
    }
}

async function handleFormSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(questForm);
    const questData = Object.fromEntries(formData.entries());
    
    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(questData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to create quest');
        }
        
        // Reload quests and hide form
        await loadQuests();
        hideQuestForm();
    } catch (error) {
        console.error('Error creating quest:', error);
        alert(`Failed to create quest: ${error.message}`);
    }
}

async function toggleQuestCompletion(questId, completed) {
    try {
        const response = await fetch(`${API_URL}/${questId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ completed })
        });
        
        if (!response.ok) throw new Error('Failed to update quest');
        
        await loadQuests();
    } catch (error) {
        console.error('Error updating quest:', error);
        alert('Failed to update quest. Please try again later.');
    }
}

async function deleteQuest(questId) {
    if (!confirm('Are you sure you want to delete this quest?')) return;
    
    try {
        const response = await fetch(`${API_URL}/${questId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete quest');
        
        await loadQuests();
    } catch (error) {
        console.error('Error deleting quest:', error);
        alert('Failed to delete quest. Please try again later.');
    }
}
