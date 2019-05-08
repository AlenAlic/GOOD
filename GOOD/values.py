# Environments
DEVELOPMENT_ENV = 'development'
DEBUG_ENV = 'debug'
TESTING_ENV = 'testing'
PRODUCTION_ENV = 'production'
TESTING_ENVIRONMENTS = [DEVELOPMENT_ENV, TESTING_ENV, DEBUG_ENV]

# METHODS
GET = "GET"
POST = "POST"
PUT = "PUT"
PATCH = "PATCH"

# ACCESS
ADMIN = 'admin'
ADJUDICATOR = 'adjudicator'


ACCESS = {
    ADMIN: 0,
    ADJUDICATOR: 10,
}


# Grade
def calculate_grade(number):
    return number*0.5+5


# DEFAULTS
LEAD = "Lead"
FOLLOW = "Follow"
FINAL_GRADE = "Final grade"
# Levels
D_LEVEL = 'D'
C_LEVEL = 'C'
B_LEVEL = 'B'
A_LEVEL = 'A'
LEVELS = [D_LEVEL, C_LEVEL, B_LEVEL, A_LEVEL]
# Disciplines
BALLROOM = 'Ballroom'
STANDARD = 'Standard'
LATIN = 'Latin'
# Dances
SLOW_WALTZ = "Slow Waltz"
TANGO = "Tango"
VIENNESE_WALTZ = "Viennese Waltz"
SLOW_FOXTROT = "Slow Foxtrot"
QUICKSTEP = "Quickstep"
SAMBA = "Samba"
CHA_CHA_CHA = "Cha Cha Cha"
RUMBA = "Rumba"
PASO_DOBLE = "Paso Doble"
JIVE = "Jive"
DANCES_TAGS = {
    SLOW_WALTZ: "SW",
    TANGO: "TG",
    VIENNESE_WALTZ: "VW",
    SLOW_FOXTROT: "SF",
    QUICKSTEP: "QS",
    SAMBA: "SB",
    CHA_CHA_CHA: "CC",
    RUMBA: "RB",
    PASO_DOBLE: "PD",
    JIVE: "JV",
}
STANDARD_DANCES = [SLOW_WALTZ, TANGO, VIENNESE_WALTZ, SLOW_FOXTROT, QUICKSTEP]
LATIN_DANCES = [SAMBA, CHA_CHA_CHA, RUMBA, PASO_DOBLE, JIVE]
BASIC_DANCES = [SLOW_WALTZ, TANGO, QUICKSTEP, CHA_CHA_CHA, RUMBA, JIVE]
MANDATORY_DANCES = {
    C_LEVEL: [SLOW_WALTZ, TANGO, VIENNESE_WALTZ, QUICKSTEP, SAMBA, CHA_CHA_CHA, RUMBA, JIVE],
    B_LEVEL: [SLOW_WALTZ, TANGO, VIENNESE_WALTZ, SLOW_FOXTROT, QUICKSTEP, SAMBA, CHA_CHA_CHA, RUMBA, PASO_DOBLE, JIVE],
    A_LEVEL: [SLOW_WALTZ, TANGO, VIENNESE_WALTZ, SLOW_FOXTROT, QUICKSTEP, SAMBA, CHA_CHA_CHA, RUMBA, PASO_DOBLE, JIVE]
}


# Dancers
DANCERS = [
    "Anthony Noble",
    "Kayley Gates",
    "Jean Lang",
    "Samuel Redfern",
    "Sherry Vaughn",
    "Zayn Black",
    "Sammy Prince",
    "Bella-Rose Mathis",
    "Aaliyah Valentine",
    "Drew Sampson",
    "Ahmed David",
    "Ryder Lamb",
    "Fionn Irvine",
    "Nadine Ratcliffe",
    "George O'Gallagher",
    "Eduard Hays",
    "Dua Macfarlane",
    "Berat Bevan",
    "Amara Knowles",
    "Ayla Morse",
    "Elsie-May Hunter",
    "Ritik Rees",
    "Joseph Garza",
    "Roma Farmer",
    "Angel Key",
    "Lyla Mackie",
    "Nellie Haigh",
    "Crystal Howarth",
    "Sameera Snyder",
    "Marguerite Keith",
    "Sienna-Rose Goodwin",
    "Johnnie Mueller",
    "Rahima Hanna",
    "Abiha Caldwell",
    "Hettie Rocha",
    "Roisin Figueroa",
    "Maxwell Dejesus",
    "Lleyton Riggs",
    "Celeste Tyson",
    "Amalie Burt",
    "Katlyn Orr",
    "Elisha Bowler",
    "Archie Nash",
    "Amiya Hyde",
    "Ruqayyah Caldwell",
    "Ross Pearce",
    "Kofi Willis",
    "Charles Fowler",
    "Cem Hubbard",
    "Abigail Greer",
    "Caoimhe Adamson",
    "Usama Vaughan",
    "Amy-Louise Cameron",
    "Carlton Gillespie",
    "Marissa Bird",
    "Leticia Rose",
    "Dianne Bain",
    "Arianna Pineda",
    "Carolina Leach",
    "Imani Garrett",
    "Farzana Gomez",
    "Mysha Warren",
    "Asif Juarez",
    "Samson Mullen",
    "Caleb Currie",
    "Antony Duke",
    "Bryony Brandt",
    "Talia Andersen",
    "Yu Finley",
    "Atticus Huff",
    "Ariana Valenzuela",
    "Jozef Sharpe",
    "Marcie Werner",
    "Jadene Petty",
    "Danika Armstrong",
    "Willa Salt",
    "Saad Adams",
    "Keiron Metcalfe",
    "Shayna Brewer",
    "Aqsa Shepard",
    "Kaidan Reyna",
    "Tariq Joseph",
    "Suzanne Austin",
    "Varun Thompson",
    "Faiza Zimmerman",
    "Octavia Winter",
    "Kiki Webster",
    "Kaelan Esquivel",
    "Martine Betts",
    "Keely Edwards",
    "Brandy Allen",
    "Moesha Ayers",
    "Danny Shields",
    "Blossom Wilson",
    "Kacy Barrow",
    "Tomasz Burke",
    "Zack Goldsmith",
    "Kaison Moran",
    "Primrose Porter",
    "Shakeel Reyes",
    "Abraham Davison",
    "Willard Gamble",
    "Coen Byrne",
    "Millie-Mae Lucero",
    "Denise Walker",
    "Orla Bautista",
    "Monet Haigh",
    "Florence Herbert",
    "Rebecca Flynn",
    "Chante Holden",
    "Jazmyn Ahmed",
    "Mirza Truong",
    "Lawrence Christie",
    "Kay Odling",
    "Liberty Durham",
    "Bertie Devlin",
    "Sabah Brandt",
    "Juno O'Sullivan",
    "Benn Goulding",
    "Leila Bryan",
    "Derek Couch",
    "Aliesha Mcdowell",
    "Mylah Callaghan",
    "Alana Mccormick",
    "Jordan-Lee Hess",
    "Adem Price",
    "Chad Dennis",
    "Mea Sparks",
    "Faiz Hendricks",
    "Andreea Bourne",
    "Mariella Crowther",
    "Alvin Caldwell",
    "Reece Mathis",
    "Carmel Xiong",
    "Farhan Rivas",
    "Tylor Allman",
    "Emilis Hunter",
    "Safiyyah Dotson",
    "Cindy Andrade",
    "Eathan Chen",
    "Leilani Chavez",
    "Ronnie Hawkins",
    "Priyanka Tran",
    "Hallam Terry",
    "Tiana Flores",
    "Roshan David",
    "Gregg Bentley",
    "Roger Griffiths",
    "Ajay Dalby",
    "Lester Leon",
    "Owain Johnston",
    "Keaton Paine",
    "Vera Pineda",
    "Charis Richmond",
    "Theodora Rawlings",
    "Danyal Adkins",
    "Phillip Mullins",
    "Amelia-Grace Regan",
    "Jaden Simon",
    "Kris Briggs",
    "Niamh Lucas",
    "Faraz Lott",
    "Xena Curran",
    "Hammad Morrow",
    "Rosalie Connelly",
    "Tyreece Beasley",
    "Hugh Morales",
    "Hareem Huerta",
    "Akeem Bishop",
    "Jem Yang",
    "Leena Cash",
    "Maximus Fritz",
    "Habiba Underwood",
    "Oluwatobiloba Sheridan",
    "Rosa Buchanan",
    "Uzair Abbott",
    "Ahsan Molina",
    "Antonio Marshall",
    "Saarah Forrest",
    "Abi Bruce",
    "Eddie Quintero",
    "Haya Rooney",
    "Zayn Velez",
    "Neel Langley",
    "Shae Swift",
    "Loretta Willis",
    "Emilia Ryder",
    "Tymon Reeves",
    "Saeed Murray",
    "Geraint Mccarthy",
    "Mateusz Patton",
    "Isaiah Dunn",
    "Amy-Leigh Frederick",
    "Jeff Sampson",
    "Eren Holman",
    "Wren Begum",
    "Zohaib Sandoval",
    "Mike Berg",
    "Omer Thatcher",
    "Matas Sheldon",
]