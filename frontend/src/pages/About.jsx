import TeamMember from "../components/TeamMember/TeamMember";
import team from '../data/team';

function About() {
    return(
        <>
        <div className ="banner"> 
          <h1 className="banner-title">About CareerGPS</h1>
          <p>Navigate your career with confidence</p>
        </div>

        <div className="about-section">
          <div className="us box">
            <h1 className="box-header">Who We Are</h1>
            <p className="box-body">
              We are a team of computer science students passionate about bridging the gap
              between higher education and the modern job market. As a team full of seniors,
              we know firsthand how overwhelming it can be to get started on a career path.
              That is why we create CareerGPS! We wanted to build an intuitive web application
              that simplifies the journey and help our peers get their foot in the door confidently.
              By transforming academic backgrounds and personal goals into clear, actionable career
              pathways and professional resumes, we are here to ensure the nos student has to navigate 
              their future without a map.
            </p>
          </div>

          <div className="about-details">
            <div className="box">
              <h1 className="box-header">Our Mission</h1>
              <p className="box-body">
                Our focus is to eliminate the guesswork from the college-to-career transition.
                Our team is dedicated to providing students with accessible, data-driven navigation tools
                to find a clear post-graduation trajectory. With structured guidance, we plan to empower
                every student to confidently kickstart their professional journeys.
              </p>
            </div>
            <div className="box">
              <h1 className="box-header">Our Vision</h1>
              <p className="box-body">
                Our vision is a world where no degree goes to waste and every student has a clear route
                to their dream job! We aim to become a digital compass for higher education and ensure that 
                any student enters their desired career with ease.
              </p>
            </div>
          </div>

        </div>

        <div className="banner">
          <h1>Meet Our Team!</h1>
        </div>

        <div className="team">
          {team.map(member => (
            <TeamMember
            key={member.name}
            photo={member.photo}
            name={member.name}
            role={member.role}
            bio={member.bio}
            github={member.github}
            />
          ))}
        </div>

        <div className="about-section">
          <div className="box meet">
            <h1 className="box-header">Team Meetings</h1>
            <ul>
              <li className="box-body meet-deet">
                Our team is scheduled to meet twice a week: Once during in person classes
                on Tuesdays (1:00 PM - 3:45 PM) and once over discord on Thursdays (1:00 PM)
              </li>

              <li className="box-body meet-deet">
                Extra meetings will be arranged as needed
              </li>

              <li className="box-body meet-deet">
                All extra communicaitons and collaboration can be coordinated through the
                team Discord server
              </li>
            </ul>

          </div>
        </div>
        </>
    );
}

export default About;