from io import BytesIO
# import uvicorn
# from fastapi import FastAPI, Request, HTTPException
# from fastapi.responses import JSONResponse
# from json import loads
from openai import OpenAI
from pymongo import MongoClient
from langchain_openai import OpenAIEmbeddings
from langchain_mongodb import MongoDBAtlasVectorSearch
from flask import Flask, request , jsonify
app = Flask(__name__)

# app = FastAPI()

# Initialize OpenAI client
openAiClient = OpenAI(api_key="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")

# MongoDB setup
MONGO_URI = 'mongodb+srv://Kunal:Udhyam123@udhyamrag.8eygtkb.mongodb.net/?retryWrites=true&w=majority&appName=udhyamRag'
MONGO_DB = 'Rag_Udhyam'
MONGO_COLLECTION = 'rag_udhyam' 
client = MongoClient(MONGO_URI,connect=False)
db = client[MONGO_DB]
collection = db[MONGO_COLLECTION]   

# 2nd api to process user question

# @app.post("/get_question/")
@app.route("/get_question_staging", methods=["POST"])
# add user_question:Request as argument in function before deploying
def get_question_staging():
    try:
        print("at top ")       
        data = request.get_json()
        question =str(data.get('question')) 
        old_prompt =  str(data.get('prompt'))
        state = str(data.get('state'))
        content_language = str(data.get('language'))
        language = ""
        if content_language == "HI":
           language = "Hindi language in Devanagiri Script (HI)"
        elif content_language == "PA-EN":
           language = "Punjabi language in English Script"
        elif content_language == "HI-EN":
           language = "Hindi language in English Script"
        elif content_language == "PA":
           language = "Punjabi language in Gurmukhi Script"
        else:
           language = "English language"

        prompt = old_prompt +" "+ f"Respond in {language}."
        
        print("body",question,prompt,content_language,state)
        embeddings_model = OpenAIEmbeddings(
            disallowed_special=(),
            api_key="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",
            model="text-embedding-ada-002",
        )
        vector_search = MongoDBAtlasVectorSearch(
            collection=collection, index_name="vector_index", embedding=embeddings_model
        )
        pre_filter = {'state': state}
        print("pre_filter",pre_filter)
        question_language =  get_language(question)
        if question_language == "EN":
          results = vector_search.similarity_search_with_score(query=question, k=3, pre_filter = pre_filter)
        else:
         results = vector_search.similarity_search_with_score(query=question_language, k=3 , pre_filter=pre_filter)

        chunked_prompt = ""
        for i in results:
          page_content = i[0].page_content
          chunked_prompt += " " + page_content
                                                                 
        gpt_data =  chatgpt_call(prompt, question, chunked_prompt)
        print("Done with getting gpt response",gpt_data)
        # This part is done to add the data in a particular format.
        edited_chunked_prompt = f"\n{prompt}\n*Chunk* :\n {chunked_prompt}\n"
        # client.close()
        # print("type",type({'gpt_response': gpt_data, "chunk": chunked_prompt}))
        return jsonify({'gpt_response': gpt_data , "chunk":edited_chunked_prompt})
    except Exception as e:
        return jsonify(status_code=500, detail=f"An error occurred in get_question: {e}")

def chatgpt_call(prompt, question, chunk):
    try:
        prompt = prompt + chunk
        result =  openAiClient.chat.completions.create(model='gpt-4o',messages=[{'role':'system','content':prompt},{
         'role':'user','content':question
     }],temperature=0,max_tokens=1500,top_p=1,presence_penalty=0,frequency_penalty=0)
        response = result.choices[0].message.content
        return response
    except Exception as e:
        error_message = f'An error occurred in chatgpt_call: {str(e)}'
        return {'error': error_message}

def get_language(question):
    try:
        prompt ='You will be provided with a body of text. Your job is to classify it into a language code based on the language it is written in. The codes and corresponding language scripts are: 1. English (EN) 2. Hindi in Devanagiri Script (HI) 3. Hindi in English Script (HI-EN) 4. Punjabi in Gurmukhi Script (PA) 5. Punjabi in English Script (PA-EN) 6. Telugu in Telugu Lipi (TE) 7. Telugu in English Script (TE-EN) You will provide two output the language(only language not code) of the text in which it is written and if the text is not written in English then convert the text to English and then provide the text as output else provide the text as it is '

        result =  openAiClient.chat.completions.create(model='gpt-4o',messages=[{'role':'system','content':prompt},{
         'role':'user','content':question
     }],temperature=0,max_tokens=1500,top_p=1,presence_penalty=0,frequency_penalty=0)
        response = result.choices[0].message.content
        # print("language", response)
        return response
    except Exception as e:
        error_message = f'An error occurred in get_language: {str(e)}'
        return {'error': error_message}

if __name__ == "__main__":
    app.run( debug=True,host="127.0.0.1", port=8000)



# To run the code locally , first install venv -->  
# uncomment last two lines of code 
# if __name__ == "__main__":
# uvicorn.run(app, host="127.0.0.1", port=8080)
# write command python -m venv venv 
# then install requirements.txt 
# python install requirements.txt
# activate virtual environment
# venv/Scripts/activate
# run code
# python main.py