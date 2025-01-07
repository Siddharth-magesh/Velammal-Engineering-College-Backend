from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['VEC']  

def insert_student_activities_data():
    collection = db['student_activities']  

    documents = [
        {
            "dept_id": 1,
            "content": "Students' achievements are a testament to their hard work, dedication, and resilience in the pursuit of academic and personal growth. From excelling in academics and securing top grades to showcasing talent in sports, arts, and extracurricular activities, their accomplishments reflect a well-rounded development. Participation in science fairs, debates, and cultural events highlights their creativity and critical thinking, while community service projects demonstrate their commitment to making a positive impact. These achievements not only inspire their peers but also pave the way for future opportunities, building confidence and a strong foundation for lifelong success.",
            "images": [
                {"image_path": "path/to/image1_1.jpg", "image_content": "AI&DS Department Paper Presentation (2nd Prize)", "event_name": "III year students of the AI&DS department won second prize in the paper presentation held at Saveetha Engineering College on 23.08.24. Paper Title: 'Are Women Safe in India?", "date": "2024-08-23"},
                {"image_path": "path/to/image1_2.jpg", "image_content": "AI&DS Department Paper Presentation (2nd Prize)", "event_name": "III year students of our department won second prize in the paper presentation held at Saveetha Engineering College on 23.08.24. Paper Title: 'Preventing Fake Social Media Profiles and Reporting", "date": "2024-08-23"},
                {"image_path": "path/to/image1_3.jpg", "image_content": "AI&DS Department Paper Presentation (1st Prize)", "event_name": "III year students, Vasantha Raja and Roshan Varghese, won 1st prize in the Paper Presentation held at Saveetha Engineering College on 27/8/2024. They were awarded a trophy and a cash prize of Rs.1000.", "date": "2024-08-27"},
                {"image_path": "path/to/image1_4.jpg", "image_content": "AI&DS Department IPL Auction Event", "event_name": "II year student Tharun. M participated in the IPL Auction event conducted by the Mechanical Department of Velammal Engineering College and won First place with a prize of Rs.1500", "date": "2024-08-24"},
                {"image_path": "path/to/image1_5.jpg", "image_content": "Technoxian World Cup Participation", "event_name": "AI&DS Department student T. Vishal Raj of Final year participated in the Maze Solver Challenge of Technoxian World Cup 2024, held at Noida Stadium Complex, Noida from 24th-27th August 2024.", "date": "2024-08-24"},
                {"image_path": "path/to/image1_6.jpg", "image_content": "AI&DS Department Football Tournament", "event_name": "AI&DS Department student Lokharajan of III year won third place in the football tournament conducted by Velammal Institute of Technology.", "date": "2024-09-01"},
                {"image_path": "path/to/image1_7.jpg", "image_content": "CM Trophy Basketball Match", "event_name": "AI&DS Department student Mugunthan Balaji from II year achieved Runner-up in the CM Trophy basketball match conducted at __________________.", "date": "2024-09-05"},
                {"image_path": "path/to/image1_8.jpg", "image_content": "INNOTHON-24 Hackathon", "event_name": "AI&DS Department students Pranesh Kumar, Siddarth, Sriram, Arjun, and Mohamed Yasir won First Place in the Hackathon (INNOTHON-24) conducted by KCG College of Engineering and won a cash prize of Rs.25000 on 21-9-2024.", "date": "2024-09-21"},
                {"image_path": "path/to/image1_9.jpg", "image_content": "Zonal Level Volleyball Tournament", "event_name": "AI&DS Department II year student Thamizhvendhan won 3rd place in the Zonal level volleyball tournament conducted by RMK Engineering College on 26-9-2024.", "date": "2024-09-26"},
                {"image_path": "path/to/image1_10.jpg", "image_content": "Zonal Level Basketball Tournament", "event_name": "AI&DS Department II year student Mugunthan Balaji won 2nd place in the Zonal level basketball tournament conducted by RMK Engineering College on 26-9-2024.", "date": "2024-09-26"}
            ]
        },
        {
            "dept_id": 2,
            "content": "Department 2 Content",
            "images": [
                {"image_path": "path/to/image2_1.jpg", "image_content": "Description of Image 2_1", "event_name": "Event 2_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_2.jpg", "image_content": "Description of Image 2_2", "event_name": "Event 2_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_3.jpg", "image_content": "Description of Image 2_3", "event_name": "Event 2_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_4.jpg", "image_content": "Description of Image 2_4", "event_name": "Event 2_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_5.jpg", "image_content": "Description of Image 2_5", "event_name": "Event 2_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_6.jpg", "image_content": "Description of Image 2_6", "event_name": "Event 2_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_7.jpg", "image_content": "Description of Image 2_7", "event_name": "Event 2_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_8.jpg", "image_content": "Description of Image 2_8", "event_name": "Event 2_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_9.jpg", "image_content": "Description of Image 2_9", "event_name": "Event 2_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image2_10.jpg", "image_content": "Description of Image 2_10", "event_name": "Event 2_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 3,
            "content": "Department 3 Content",
            "images": [
                {"image_path": "path/to/image3_1.jpg", "image_content": "Description of Image 3_1", "event_name": "Event 3_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_2.jpg", "image_content": "Description of Image 3_2", "event_name": "Event 3_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_3.jpg", "image_content": "Description of Image 3_3", "event_name": "Event 3_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_4.jpg", "image_content": "Description of Image 3_4", "event_name": "Event 3_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_5.jpg", "image_content": "Description of Image 3_5", "event_name": "Event 3_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_6.jpg", "image_content": "Description of Image 3_6", "event_name": "Event 3_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_7.jpg", "image_content": "Description of Image 3_7", "event_name": "Event 3_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_8.jpg", "image_content": "Description of Image 3_8", "event_name": "Event 3_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_9.jpg", "image_content": "Description of Image 3_9", "event_name": "Event 3_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image3_10.jpg", "image_content": "Description of Image 3_10", "event_name": "Event 3 _10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 4,
            "content": "Department 4 Content",
            "images": [
                {"image_path": "path/to/image4_1.jpg", "image_content": "Description of Image 4_1", "event_name": "Event 4_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_2.jpg", "image_content": "Description of Image 4_2", "event_name": "Event 4_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_3.jpg", "image_content": "Description of Image 4_3", "event_name": "Event 4_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_4.jpg", "image_content": "Description of Image 4_4", "event_name": "Event 4_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_5.jpg", "image_content": "Description of Image 4_5", "event_name": "Event 4_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_6.jpg", "image_content": "Description of Image 4_6", "event_name": "Event 4_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_7.jpg", "image_content": "Description of Image 4_7", "event_name": "Event 4_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_8.jpg", "image_content": "Description of Image 4_8", "event_name": "Event 4_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_9.jpg", "image_content": "Description of Image 4_9", "event_name": "Event 4_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_10.jpg", "image_content": "Description of Image 4_10", "event_name": "Event 4_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 5,
            "content": "Department 4 Content",
            "images": [
                {"image_path": "path/to/image4_1.jpg", "image_content": "Description of Image 4_1", "event_name": "Event 4_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_2.jpg", "image_content": "Description of Image 4_2", "event_name": "Event 4_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_3.jpg", "image_content": "Description of Image 4_3", "event_name": "Event 4_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_4.jpg", "image_content": "Description of Image 4_4", "event_name": "Event 4_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_5.jpg", "image_content": "Description of Image 4_5", "event_name": "Event 4_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_6.jpg", "image_content": "Description of Image 4_6", "event_name": "Event 4_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_7.jpg", "image_content": "Description of Image 4_7", "event_name": "Event 4_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_8.jpg", "image_content": "Description of Image 4_8", "event_name": "Event 4_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_9.jpg", "image_content": "Description of Image 4_9", "event_name": "Event 4_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_10.jpg", "image_content": "Description of Image 4_10", "event_name": "Event 4_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 5,
            "content": "Department 4 Content",
            "images": [
                {"image_path": "path/to/image4_1.jpg", "image_content": "Description of Image 4_1", "event_name": "Event 4_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_2.jpg", "image_content": "Description of Image 4_2", "event_name": "Event 4_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_3.jpg", "image_content": "Description of Image 4_3", "event_name": "Event 4_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_4.jpg", "image_content": "Description of Image 4_4", "event_name": "Event 4_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_5.jpg", "image_content": "Description of Image 4_5", "event_name": "Event 4_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_6.jpg", "image_content": "Description of Image 4_6", "event_name": "Event 4_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_7.jpg", "image_content": "Description of Image 4_7", "event_name": "Event 4_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_8.jpg", "image_content": "Description of Image 4_8", "event_name": "Event 4_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_9.jpg", "image_content": "Description of Image 4_9", "event_name": "Event 4_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image4_10.jpg", "image_content": "Description of Image 4_10", "event_name": "Event 4_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 6,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 7,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 8,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 9,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 10,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 11,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image _path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 12,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 13,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_ 2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 14,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        },
        {
            "dept_id": 15,
            "content": "Department 5 Content",
            "images": [
                {"image_path": "path/to/image5_1.jpg", "image_content": "Description of Image 5_1", "event_name": "Event 5_1", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_2.jpg", "image_content": "Description of Image 5_2", "event_name": "Event 5_2", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_3.jpg", "image_content": "Description of Image 5_3", "event_name": "Event 5_3", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_4.jpg", "image_content": "Description of Image 5_4", "event_name": "Event 5_4", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_5.jpg", "image_content": "Description of Image 5_5", "event_name": "Event 5_5", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_6.jpg", "image_content": "Description of Image 5_6", "event_name": "Event 5_6", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_7.jpg", "image_content": "Description of Image 5_7", "event_name": "Event 5_7", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_8.jpg", "image_content": "Description of Image 5_8", "event_name": "Event 5_8", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_9.jpg", "image_content": "Description of Image 5_9", "event_name": "Event 5_9", "date": "YYYY-MM-DD"},
                {"image_path": "path/to/image5_10.jpg", "image_content": "Description of Image 5_10", "event_name": "Event 5_10", "date": "YYYY-MM-DD"}
            ]
        }
    ]

    collection.insert_many(documents)