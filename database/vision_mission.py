from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")

db = client["VEC"]

def insert_department_data():
    collection = db["vision_and_mission"]

    departments = [
        {
            "department_id": 1,
            "department_name": "Artificial Intelligence and Data Science",
            "department_image": "url_to_ai_ds_image",
            "department_quotes": "Empowering innovation through data-driven intelligence.",
            "vision": "To achieve value based education and bring idealistic, ethical engineers to meet the thriving trends and technology in the field of Artificial Intelligence and Data Science",
            "mission": [
                "To engage students with the core competence to solve real world problems using Artificial Intelligence.",
                "To enlighten students into technically proficient engineers through innovation in Data Science.",
                "To involve students with industry collaboration, career guidance and leadership skills.",
                "To mould students as ethical professionals to bring morals to individual and society."
            ],
            "about_department": "Department of Artificial Intelligence aims to produce computing graduates with high potency, apply, design and develop systems to pertain and to integrate both software and hardware devices, utilize modern approaches in programming and problem solving techniques. The Department was established in the year 2020 with the main objective of providing quality education in the field of Engineering and Technology. It is recognized as nodal center under Anna University. The Department has proved to be a center of excellence in Academic, Sponsored research and Continuing Education Programme."
        },
        {
            "department_id": 2,
            "department_name": "Automobile Engineering",
            "department_image": "url_to_cse_image",
            "department_quotes": "Innovating the future of technology.",
            "vision": "To excel in computer science education, research, and innovation.",
            "mission": [
                "Deliver quality education in computer science engineering.",
                "Foster research in emerging fields of technology.",
                "Build industry-ready professionals with strong ethical values."
            ],
            "about_department": "The department emphasizes core computing skills and modern engineering practices."
        },
        {
            "department_id": 3,
            "department_name": "Chemistry ",
            "department_image": "url_to_it_image",
            "department_quotes": "Transforming information into solutions.",
            "vision": "To be a leader in IT education and innovation, bridging technology and business.",
            "mission": [
                "Impart theoretical and practical knowledge in IT.",
                "Promote research in information systems and technologies.",
                "Encourage entrepreneurship and innovation."
            ],
            "about_department": "The department bridges the gap between technology and practical implementation."
        },
        {
            "department_id": 4,
            "department_name": "Civil Engineering",
            "department_image": "url_to_cybersecurity_image",
            "department_quotes": "Securing the digital world.",
            "vision": "To be a leader in cybersecurity education and research, ensuring a safer digital environment.",
            "mission": [
                "Provide a comprehensive understanding of cybersecurity concepts.",
                "Conduct research in emerging threats and solutions.",
                "Train professionals to safeguard information and systems."
            ],
            "about_department": "The department focuses on equipping students with skills to tackle modern cybersecurity challenges."
        },
        {
            "department_id": 5,
            "department_name": "Computer Science & Engineering   ",
            "department_image": "url_to_ece_image",
            "department_quotes": "Connecting the world through innovation.",
            "vision": "To pioneer in electronics and communication engineering education and research.",
            "mission": [
                "Develop expertise in electronics and communication technologies.",
                "Promote innovative research for societal benefits.",
                "Prepare students for leadership roles in industry and academia."
            ],
            "about_department": "The department specializes in modern communication systems and electronic design."
        },
        {
            "department_id": 6,
            "department_name": "Computer Science and Engineering (CYBER SECURITY)   ",
            "department_image": "url_to_eee_image",
            "department_quotes": "Powering the future.",
            "vision": "To excel in electrical and electronics engineering education and sustainable innovation.",
            "mission": [
                "Provide a strong foundation in electrical and electronics engineering.",
                "Encourage research in renewable energy and smart systems.",
                "Equip students with problem-solving skills for the energy sector."
            ],
            "about_department": "The department addresses challenges in energy systems and electrical technologies."
        },
        {
            "department_id": 7,
            "department_name": "Electrical & Electronics Engineering   ",
            "department_image": "url_to_eie_image",
            "department_quotes": "Precision engineering for a better world.",
            "vision": "To lead in electronic and instrumentation engineering education and innovation.",
            "mission": [
                "Focus on quality education in instrumentation and control systems.",
                "Promote research in automation and intelligent systems.",
                "Prepare students for industrial and academic excellence."
            ],
            "about_department": "The department emphasizes control systems and precision technologies."
        },
        {
            "department_id": 8,
            "department_name": "Electronics & Instrumentation Engineering ",
            "department_image": "url_to_civil_image",
            "department_quotes": "Building the foundation for tomorrow.",
            "vision": "To be a leader in civil engineering education, research, and sustainable development.",
            "mission": [
                "Provide in-depth knowledge of civil engineering principles.",
                "Encourage innovation in construction and design.",
                "Promote sustainable and eco-friendly engineering practices."
            ],
            "about_department": "The department focuses on modern construction technologies and sustainability."
        },
        {
            "department_id": 9,
            "department_name": "Electronics and Communication Engineering ",
            "department_image": "url_to_mechanical_image",
            "department_quotes": "Engineering the tools of the future.",
            "vision": "To achieve excellence in mechanical engineering education and research.",
            "mission": [
                "Deliver comprehensive knowledge of mechanical systems.",
                "Promote research in advanced manufacturing and materials.",
                "Prepare students for global challenges in engineering."
            ],
            "about_department": "The department emphasizes mechanical system design and innovation."
        },
        {
            "department_id": 10,
            "department_name": "English ",
            "department_image": "url_to_automobile_image",
            "department_quotes": "Driving innovation forward.",
            "vision": "To be a center of excellence in automobile engineering education and innovation.",
            "mission": [
                "Provide expertise in automotive technologies.",
                "Encourage research in sustainable and electric vehicles.",
                "Prepare industry-ready professionals for the automotive sector."
            ],
            "about_department": "The department focuses on automotive design and sustainable transportation."
        },
        {
            "department_id": 11,
            "department_name": "Information Technology",
            "department_image": "url_to_english_image",
            "department_quotes": "Communicating the world with clarity and creativity.",
            "vision": "To enhance linguistic and literary skills for global communication and cultural understanding.",
            "mission": [
                "Promote excellence in English language and literature.",
                "Foster critical thinking and creativity through language.",
                "Prepare students for effective communication in diverse contexts."
            ],
            "about_department": "The department focuses on linguistic proficiency and literary appreciation."
        },
        {
            "department_id": 12,
            "department_name": "Mathematics",
            "department_image": "url_to_chemistry_image",
            "department_quotes": "Exploring the building blocks of matter.",
            "vision": "To excel in chemical education and research for sustainable development.",
            "mission": [
                "Provide in-depth knowledge of chemical principles.",
                "Encourage research in green and sustainable chemistry.",
                "Prepare students for careers in chemical industries and research."
            ],
            "about_department": "The department emphasizes chemical analysis and sustainable practices."
        },
        {
            "department_id": 13,
            "department_name": "Mechancial Engineering",
            "department_image": "url_to_mathematics_image",
            "department_quotes": "Unlocking the power of numbers and logic.",
            "vision": "To be a leader in mathematical education and research, fostering analytical and problem-solving skills.",
            "mission": [
                "Provide a strong foundation in mathematical concepts.",
                "Encourage interdisciplinary research involving mathematics.",
                "Equip students with analytical skills for diverse applications."
            ],
            "about_department": "The department focuses on pure and applied mathematical sciences."
        },
        {
            "department_id": 14,
            "department_name": "Physical Education",
            "department_image": "url_to_physics_image",
            "department_quotes": "Unveiling the mysteries of the universe.",
            "vision": "To excel in physics education and research, inspiring scientific curiosity.",
            "mission": [
                "Provide a strong foundation in fundamental and applied physics.",
                "Encourage research in emerging areas of physical sciences.",
                "Prepare students for careers in academia, industry, and research."
            ],
            "about_department": "The department emphasizes understanding and applying the principles of physics."
        },
        {
            "department_id": 15,
            "department_name": "Physics",
            "department_image": "url_to_biotech_image",
            "department_quotes": "Harnessing life sciences for a better tomorrow.",
            "vision": "To lead in biotechnology education and research for sustainable development.",
            "mission": [
                "Provide comprehensive knowledge in biotechnology.",
                "Encourage research in genetic engineering and bioprocess technology.",
                "Prepare students for global challenges in biotechnology and healthcare."
            ],
            "about_department": "The department focuses on cutting-edge research in life sciences and biotechnology applications."
        }
    ]

    collection.insert_many(departments)