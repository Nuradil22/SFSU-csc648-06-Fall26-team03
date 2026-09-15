import './TeamMember.css'

function TeamMember({photo, name, role, bio, github}) {
    return (
        <div className="team-member">
            <a href={github} target="_blank" rel="noopener noreferrer" class="github-linker">
            <img src={photo} alt={name} />
            <h2>{name}</h2>
            <h3 class="role">{role}</h3>
            <div className="bio-container">
                <span class="trigger-txt">See bio...</span>
                <span className="bio">{bio}</span>
            </div>
            </a>
        </div>
    );
}

export default TeamMember;