import './Footer.css';
import { NavLink } from 'react-router-dom'

function Footer(){
    return(
        <footer className="footer">
            <div className="footer-column">
                <h1><span className="underline">Account</span></h1>
                <NavLink to="/account/setup" end>
                    Account Setup
                </NavLink>

                <NavLink to="/account/dashboard" end>
                    Dashboard
                </NavLink>

            </div>

            <div className="footer-column">
                <h1><span className="underline">Resources</span></h1>
                <NavLink to="/resources/certificates" end>
                    SFSU Certificate Programs
                </NavLink>

                <NavLink to="/" end>
                    About Projectory
                </NavLink>
            </div>
        </footer>
    );
}

export default Footer;