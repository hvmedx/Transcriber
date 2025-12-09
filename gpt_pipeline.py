import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def summarise_and_question(chunk_text):
    """
    Envoie un texte à GPT-4o et retourne résumé + questions
    """
    if not chunk_text or len(chunk_text.strip()) < 10:
        return "Texte trop court pour analyser.\n"
    
    prompt = f"""
    Voici un texte : "{chunk_text}"
    1. Fais un résumé concis en une phrase.
    2. Pose 2 questions pertinentes pour clarifier ou approfondir les points du texte.
    
    Format de réponse:
    Résumé: [ton résumé]
    Question 1: [question]
    Question 2: [question]
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Erreur API OpenAI: {str(e)}\n"
