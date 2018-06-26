# databases_evaluation_project

This project is the newer, final version of a class evaluation system, which was an academic project for a Databases course. This version contains the comnplete functionality specified in our project requirements. 

This project was built using the Python programming language (version 3), and the Django Web Framework (version 2). The database backend used was originally MySQL, but was recently moved to PostgreSQL. The frontend was built using HTML, Javascript (JQuery and the Google Charts API in specific), and a bit of CSS. 

This system allows professors to log in to access the system. As opposed to the old version of this project, students do not have their own login credentials or homepage. Instead, the professor provides students with a "password" which they input into the course evaluation homepage, and if the password is correct, students are taken straight to the evaluation page, where they can complete and submit the evaluation. 

Professors can add courses which they teach, and the system automatically generates evaluation sessions based on the weekly evaluation times and the start and end days of the semester. The auto-generated sessions contain a randomly generated evaluation password for the students, which the Professor can change at any time. If a course's info is changed, the system will automatically create or delete evaluation session accordingly. The professor can also manually add, edit, and delete evaluation sessions and courses.

The Professor can view reports for each session, for all sessions of a course over an entire semester, and for a comparison of two sessions of the same course. Charts are also seen for every report, implemented using the Google Charts API. 

I am aware that the way this is implemented, only one Professor can use this system, and that students can submit multiple evaluations if they want, and that students outside the course can also submit evaluations. But, I was told to implement it this way by my Professor, who was concerned with student's anonymity, and felt that the best way for them to be anonymous is to not store their information at all. The way I implemented the project in the old version (which is contained in another repo here on GitHub), the system could be used by multiple professors, and only students enrolled in the course could evaluate the course, and each student can only evaluate a class once. But, I was told by my Professor to implement it this way, so that no student's anonymity is sacrificed. Personally, though, I feel that the way I implemented it in the older version is better suited as an actual sellable software product. ¯\\_(ツ)_/¯

I intended to organize the eval/views.py file into multiple files, for clarity and readability of code. But, as I was short on time, I was unable to get the multiple files to work properly, so I kept it as one file. 

I am aware that the code for the forms is quite repetitive, and that the templates could have been made much simpler using Django Forms, but I was not aware of how to use them at the time. I hope to implement them, as well as other useful Django features, in future projects. 
