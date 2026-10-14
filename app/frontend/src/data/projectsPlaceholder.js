// TODO: This obviously won't be hard coded and needs to be pulled from backend

import tapelessRule1 from "../assets/exampleProjects/exampleProject2.0.png";
import tapelessRule2 from "../assets/exampleProjects/exampleProject2.1.png";
import tapelessRule3 from "../assets/exampleProjects/exampleProject2.2.png";

import termProj1 from "../assets/exampleProjects/exampleProject3.0.jpg";
import termProj2 from "../assets/exampleProjects/exampleProject3.1.jpg";
import termProj3 from "../assets/exampleProjects/exampleProject3.2.jpg";
import termProj4 from "../assets/exampleProjects/exampleProject3.3.jpg";
import termProj5 from "../assets/exampleProjects/exampleProject3.4.png";
import termProj6 from "../assets/exampleProjects/exampleProject3.5.jpg";
import termProj7 from "../assets/exampleProjects/exampleProject3.6.jpg";

const projects = [
    {
        id: "1",
        name: "<Project Name>",
        date: "<Date>",
        type: "<Project Subject>",

        description: [
            {
                id: "overview",
                type: "paragraph",
                content: "This is where a project description would go"
            }
        ],

        images: [{}], // This section will include pictures and thumbnails of 3D assets. will probably support some sort of click to expand/open feature
        links: [{}] // external links like github repositories or YouTube video demonstrations of a project
    },
    {
        id: "2",
        name: "Tapeless Ruler",
        date: "Spring 2026",
        type: "Embedded Linux",

        description: [
            {
                id: "overview",
                type: "paragraph",
                content: "This assignment was to create a tapeless ruler using the HC-SR04 sonar sensor to determine the distance of a surface."
            },
            {
            id: "goal",
            type: "heading",
            content: "Project Goals"
            },
            {
            id: "goal-details",
            type: "list",
            items: [
                "Measure distances using electronic sensors.",
                "Display measurements in an easy-to-read format.",
                "Create a practical alternative to a traditional ruler."
            ]
            },
            {
            id: "challenges",
            type: "heading",
            content: "Challenges and Lessons Learned"
            },
            {
            id: "challenges-details",
            type: "paragraph",
            content:
                "This project provided experience with hardware integration, troubleshooting, and testing."
            }
        ],      

        images: [
            {
                src: tapelessRule1,
                alt: "Picture of completed circuit",
            },

            {
                src: tapelessRule2,
                alt: "Picture of completed circuit",
            },
            {
                src: tapelessRule3,
                alt: "Picture of the wiring diagram",
            }
        ],
        links: [
            {
                label: "Github Repository",
                url: "https://github.com/CSC615-2026-Spring/csc-615-assignment-2-tapeless-ruler-ianayala01",
                type: "github"
            },
            {
                label: "Demonstration video",
                url: "https://youtu.be/T0r2BQu5-PU",
                type: "YouTube"
            }
        ]
    },
    {
        id: "3",
        name: "CSC615 Term Project",
        date: "Spring 2026",
        type: "Embedded Linux",

        description: [
            {
                id: "overview",
                type: "paragraph",
                content: "This assignment was to create an autonomous vehicle capable of following a line, reacting to different colors in its path and avoid obstacles"
            },
            {
            id: "goal",
            type: "heading",
            content: "Project Goals"
            },
            {
            id: "goal-details",
            type: "list",
            items: [
                "Create a multi-thread program capable of reading sensors and dynamic decision making",
                "Control 4 motors independently using pulse width modulation over I2C motor hats",
                "Optimize resource utilization to minimize performance issues",
                "Write a line following algorithm"
            ]
            },
            {
            id: "challenges",
            type: "heading",
            content: "Challenges and Lessons Learned"
            },
            {
            id: "challenges-details",
            type: "paragraph",
            content:
                "This project provided experience with hardware integration, troubleshooting, and testing."
            }
        ],

        images: [
            {
                src: termProj6,
                alt: "Picture of motor assembly",
            },
            {
                src: termProj7,
                alt: "Picture of motor assembly",
            },
            {
                src: termProj1,
                alt: "Picture of motor assembly",
            },

            {
                src: termProj2,
                alt: "Picture of line sensors",
            },
            {
                src: termProj3,
                alt: "Picture of completed circuits",
            },
            {
                src: termProj4,
                alt: "Picture of the robot",
            },
            {
                src: termProj5,
                alt: "Picture of wiring diagram",
            }
        ],
        links: [
            {
                label: "Main Github Repository",
                url: "https://github.com/CSC615-2026-Spring/csc-615-assignment-2-tapeless-ruler-ianayala01",
                type: "github"
            },
            {
                label: "Motor RPM Reader Github Repository",
                url: "https://github.com/ianayala01/Motor-RPM-Reader",
                type: "github"
            },
            {
                label: "Obstacle Avoidance",
                url: "https://youtube.com/shorts/w87BMcVVJrU?feature=share",
                type: "YouTube"
            },
            {
                label: "Color React Video",
                url: "https://youtube.com/shorts/VQPMVjj6ark?feature=share",
                type: "YouTube"
            }

        ] // external links like github repositories or YouTube video demonstrations of a project
    }
]

export default projects;