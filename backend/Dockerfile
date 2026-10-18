# 1. Start from the official AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# 2. Copy our python library list into the container
COPY requirements.txt ./

# 3. Install the dependencies inside the container
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy our actual python code file into the container
COPY app.py ./

# 5. Tell AWS Lambda which function inside app.py to run when triggered
CMD ["app.lambda_handler"]