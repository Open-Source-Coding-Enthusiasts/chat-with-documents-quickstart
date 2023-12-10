### Deployment options
- **Docker** :
    - Go to docker dir and them to cpu-only or gpu and run `docker compose up -d`
- **Kubernetes**:
    - Not yet supported

Just remember to add necessary api keys for example if you want to use OpenAI models, provide OPENAI api key in docker-compose file
<hr>

### Usage

1. Check if everthing is connected correctly in **`Resources`** tab
    ![image](imgs/resources.png)

<br>

2. Upload PDF document
    ![image](imgs/upload_and_embed.png)
<br>

3. Create new chat
    ![image](imgs/start_chat.png)


<br>

4. Start Chatting, in this case using smallest possible llm (zephyr3b)
    ![image](imgs/example_query.png)
