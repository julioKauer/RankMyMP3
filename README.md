# RankMyMP3

## Overview
RankMyMP3 is a Python application designed to classify and rank music files using a user-friendly wxPython interface. The application follows the Model-View-Controller (MVC) design pattern and utilizes SQLite for data storage.

## Features
- **Binary Comparison**: Users can compare two music files and classify them based on preference.
- **Ranking Registration**: The application maintains a ranking of music files based on user ratings.
- **File Deletion to Trash**: Users can delete music files, which are sent to the trash instead of being permanently removed.
- **Tag Association**: Music files can be associated with tags for better organization and retrieval.
- **SQLite Data Storage**: All music information, including paths, ratings, and tags, is stored in an SQLite database.

## Project Structure
```
RankMyMP3
├── controllers
│   └── music_controller.py
├── models
│   └── music_model.py
├── views
│   └── music_app.py
├── utils
│   └── file_operations.py
├── data
│   └── music_ranking.db
├── main.py
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd RankMyMP3
   ```
3. Install the required packages:
   ```
   pip install wxPython send2trash
   ```

## Usage
1. Run the application:
   ```
   python main.py
   ```
2. Use the "Começar a Comparar" button to start comparing music files.
3. Use the "Ver Ranking" button to view the current rankings of the music files.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.