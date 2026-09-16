import './Navbar.css';
import logo from '../../assets/CareerGPS-logo.png';
import darkLogo from '../../assets/CareerGPS-logo-darkmode.png';
import { NavLink } from 'react-router-dom'

function Navbar({ darkMode, setDarkMode}){

    return (
        <nav className="navbar">
            <img src={darkMode ? darkLogo : logo} alt="CareerGPS logo" id="logo"/>

            <NavLink to="/" end className={({isActive}) => isActive ? "nav-btn active" : "nav-btn"}>
                Home</NavLink>

            <NavLink to="/tutors" className="nav-btn">Find a Tutor</NavLink>

            <NavLink to="/resume" className="nav-btn">Resume Help</NavLink>

            <NavLink to="/roadmap" className="nav-btn">Career Roadmap</NavLink>

            <NavLink to="/login" className={({isActive}) => isActive ? "nav-btn active" : "nav-btn"}> 
                Log In</NavLink>

            <button  className="nav-btn" onClick={() => setDarkMode(!darkMode)}>
                {darkMode ? "☀️ Light Mode" : "🌙 Dark Mode"}
            </button>
        </nav>
    );
}

export default Navbar;