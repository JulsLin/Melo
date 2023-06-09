# Melo
## Prerequisites
Ensure that you have Python installed on your system. 

## Setup

1. **Clone the repository**  
    Use the command below to clone the repository.
    ```
    git clone https://github.com/JulsLin/Melo
    ```

2. **Navigate to the project directory**  
    Use the command below to navigate into the cloned repository.
    ```
    cd Melo
    ```

3. **Create a virtual environment**  
    Create a new Python virtual environment using the command below.
    ```
    python -m venv venv
    ```

4. **Activate the virtual environment**  
    Use the command below to activate the virtual environment.
    On Windows:
    ```
    venv\Scripts\Activate
    ```
    On Unix or MacOS:
    ```
    source venv/bin/activate
    ```

5. **Install the required dependencies**  
    Use the command below to install all the required dependencies.
    ```
    pip install -r requirements.txt
    ```

## Initialize the Database

1. **Create the database tables**  
    Use the command below to create the necessary database tables.
    ```
    python .\app\create_tables.py
    ```

## Running the Application

1. **Start the application**  
    Use the command below to start the application.
    ```
    python .\app\app.py
    ```

