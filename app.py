import json
import os
import datetime
import time
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel
from rich.text import Text
import google.generativeai as genai
from rich import print as rprint
from time import sleep
from itertools import cycle

genai.configure(api_key="sample_key")
model = genai.GenerativeModel('gemini-pro')
console = Console()

def estimate_complexity(concern):
    complexity_score = len(concern.split())
    high_complexity_keywords = ["persistent", "chronic", "severe", "multiple", "unexplained", "ongoing"]
    complexity_score += sum(1 for word in high_complexity_keywords if word in concern.lower())
    
    if complexity_score <= 5:
        return 4
    elif complexity_score <= 10:
        return 6
    else:
        return 8

def save_session_data(data):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    data["timestamp"] = timestamp
    filename = f"health_session_{timestamp.replace(':', '-')}.json"
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    console.print(Panel(f"[bold]I've saved my recommendations for you to Your Diary 📕[/bold]"))

def gemini_request(prompt):
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        console.print(Panel(f"[red]Gemini API error: {str(e)}"))
        return None

def type_effect(text, delay=0.005):
    for char in text:
        print(char, end="", flush=True)
        sleep(delay)
    print()

def waiting_animation(text="Thinking to help...", duration=1):
    spinner = cycle(["|", "/", "-", "\\"])
    end_time = time.time() + duration
    while time.time() < end_time:
        console.print(f"[#5F9EA0]{text} {next(spinner)}", end="\r", style="cyan")
        sleep(0.15)
    print()  # Clear line after animation

def clean_response_text(text):
    return text.replace("*", "").replace("#", "").replace("`", "")

def parse_tree(tree_text):
    tree = {}
    current_question = None
    lines = [line.strip() for line in tree_text.splitlines() if line.strip()]
    
    for line in lines:
        if line.startswith("ASK"):
            current_question = line.split(": ")[0]
            tree[current_question] = {
                "question": line.split(": ")[1],
                "yes": None,
                "no": None
            }
        elif "->" in line and current_question:
            answer, next_step = [part.strip() for part in line.split("->")]
            if answer == "YES":
                tree[current_question]["yes"] = next_step
            elif answer == "NO":
                tree[current_question]["no"] = next_step
    return tree

def navigate_questions(tree_text):
    tree = parse_tree(tree_text)
    answers = {}
    current_node = "ASK1"
    valid_yes = {"yes", "yeah", "yea", "да", "oui", "हाँ"}
    valid_no = {"no", "nope", "нет", "non", "नहीं"}

    while current_node and "ASK" in current_node:
        if current_node not in tree:
            break
            
        question = tree[current_node]["question"] + " 🤔 "
        answer = None
        while not answer:
            type_effect(question)
            user_input = Prompt.ask(Text("", style="bold")).strip().lower()
            if user_input in valid_yes:
                answer = "YES"
            elif user_input in valid_no:
                answer = "NO"
            else:
                console.print(Panel("[#5F9EA0]Please respond with yes or no.[/#5F9EA0]"))

        answers[current_node] = {
            "question": question,
            "answer": answer
        }
        
        current_node = tree[current_node]["yes"] if answer == "YES" else tree[current_node]["no"]
        if current_node == "STOP":
            break
            
        waiting_animation("Thinking...", duration=1)
        
    return answers

def generate_decision_tree(concern):
    num_questions = estimate_complexity(concern)
    prompt = f"Generate a detailed YES/NO decision tree for assessing the health concern: {concern}. Include around {num_questions} questions. Format as 'ASK1: Question' followed by 'YES -> ASKn or STOP' and 'NO -> ASKn or STOP' on new lines. Generate questions in language you were asked. Do not change ASKs, YES, NO and other logic commands."
    tree_text = gemini_request(prompt)
    if tree_text is None:
        tree_text = """
ASK1: Has this been ongoing for more than a week?
YES -> ASK2
NO -> ASK3

ASK2: Are there any other symptoms?
YES -> ASK4
NO -> STOP

ASK3: Does it affect your daily activities?
YES -> ASK4
NO -> STOP

ASK4: Is the severity increasing?
YES -> STOP
NO -> STOP
"""
    return clean_response_text(tree_text)

def generate_recommendations(concern, answers):
    formatted_answers = "\n".join([f"Q: {data['question']} - A: {data['answer']}" for q, data in answers.items()])
    prompt = f"Based on the health concern '{concern}' and these answers:\n{formatted_answers}\n\nProvide specific recommendations in these sections:\n1. What causes it and how to relieve it ethnically and safely: 2. Lifestyle Considerations to help symptoms\n3. Local Support Resources\n4. Professional Help Indicators\n5. Doctor Visit Preparation\n6. Wellness Tips. Answer in language question were asked. Do not write any markdown (example: 'Health Recommendations:' instead of '[bold]Health Recommendations:[/bold]' etc). Support resources should be local based on the language user asked in"
    recommendations_text = gemini_request(prompt)
    if recommendations_text is None:
        recommendations_text = """
1. Lifestyle Considerations:
- Get enough sleep
- Maintain a balanced diet
- Manage stress through relaxation techniques

2. Support Resources:
- Local support groups
- Online health forums
- Wellness apps

3. When to Seek Professional Help:
- If symptoms worsen
- If new symptoms arise
- If daily life is affected

4. Preparation for Doctor Visit:
- List symptoms and duration
- Bring any relevant medical records
- Prepare questions for the doctor

5. General Wellness Tips:
- Exercise regularly
- Stay hydrated
- Avoid smoking and excessive alcohol
"""
    return clean_response_text(recommendations_text)

def main():
    console.print(Panel('''
Welcome to [bold]Poppy[/bold]! 😌

Let me know what concerns you. 💭

Enter as much as you'd like to share – [bold]no one will see it[/bold]. 🔒

If you want I'll save my answers, just ask! 📝
                        
Ask anything [bold]in your language[/bold]:
                        
¿Por qué tengo dolor de cabeza?
我头痛的原因是什么
Kwa nini kichwa changu kinauma?

...and others!
'''))
    
    while True:
        concern = Prompt.ask("[bold]What can I help you with?[/bold]")
        if concern.lower() == "quit":
            break
            
        console.print(Panel("[bold]Hmm, can I ask you something to understand you better?[/bold]"))
        waiting_animation()
        tree_text = generate_decision_tree(concern)

        # Decision tree printing for testing questions:
        # console.print(f"[bold]Decision Tree:[/bold]\n{tree_text}")
        # console.print(Panel("[#5F9EA0]Starting interactive question session..."))

        answers = navigate_questions(tree_text)
        
        console.print(Panel("[bold]Collecting thoughts to give you grounded recommendations...[/bold]"))
        waiting_animation()
        recommendations = generate_recommendations(concern, answers)
        type_effect("Health Recommendations:\n" + recommendations)
        
        session_data = {
            "concern": concern,
            "answers": answers,
            "recommendations": recommendations,
            "notes": ""
        }
        save_session_data(session_data)
        
        console.print(Panel("[bold]What else I can help you with?[/bold]"))

if __name__ == "__main__":
    main()
