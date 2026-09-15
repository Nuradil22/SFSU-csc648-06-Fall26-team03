import genericPfp from '../assets/Team/generic-icon.png'

import RohitBio from '../components/TeamMember/bios/RohitBio'
import RohitPfp from '../assets/Team/Rohit.jpg'

import IanPfp from '../assets/Team/Ian.jpg'
import IanBio from '../components/TeamMember/bios/IanBio'

import NuradilBio  from '../components/TeamMember/bios/NuradilBio'

import ObaidullahBio from '../components/TeamMember/bios/ObaidullahBio'
import ObaidullahPfp from '../assets/Team/Obaidullah.jpg'

const team = [
    {
        name: "Rohit Vennelakanti",
        role: "Team Lead",
        photo: RohitPfp,
        bio: RohitBio,
        github: "https://github.com/ro111t"
    },

    {
        name: "Fanta Phommachith",
        role: "Scrum Master",
        photo: genericPfp,
        bio: "<bio>",
        github: "https://github.com/fphommachith"
    },

    {
        name: "Ali Coklu",
        role: "Backend Lead",
        photo: genericPfp,
        bio: "<bio>",
        github: "https://github.com/CokluAli"
    },

    {
        name: "Nuradil Kumarov",
        role: "Github Master",
        photo: genericPfp,
        bio: NuradilBio,
        github: "https://github.com/Nuradil22"
    },

    {
        name: "Obaidullah Darwishi",
        role: "AI Master",
        photo: ObaidullahPfp,
        bio: ObaidullahBio,
        github: "https://github.com/ObaidullahDarwishi"
    },

    {
        name: "Ian Ayala",
        role: "Frontend Lead",
        photo: IanPfp,
        bio: IanBio,
        github: "https://github.com/ianayala01"
    }
];

export default team;