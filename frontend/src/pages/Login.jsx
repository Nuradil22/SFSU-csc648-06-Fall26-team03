import { useState } from "react";
import './Login.css';

import LoginForm from '../components/Forms/LoginForm';
import SignupForm from '../components/Forms/SignupForm';

import loginArtLight from '../assets/LoginArt/city-light.jpg';
import loginArtDark from '../assets/LoginArt/city-dark.jpg';

import signupArtLight from '../assets/LoginArt/bridge-light.jpg';
import signupArtDark from '../assets/LoginArt/bridge-dark.jpg';

function Login({ darkMode }) {
    const [isReturningUser, setIsReturningUser] = useState(false);

    return(
        <main className={isReturningUser ? "login-page returning" : "login-page signup"}>

            <section className="auth-panel">
                {isReturningUser ? (<LoginForm isReturningUser={isReturningUser} setIsReturningUser={setIsReturningUser}/>) : (<SignupForm isReturningUser={isReturningUser} setIsReturningUser={setIsReturningUser}/>)}
            </section>

            <section className="auth-art">
                {isReturningUser ? (<img src={darkMode ? loginArtDark : loginArtLight} alt="tbd"/>) : (<img src={darkMode ? signupArtDark : signupArtLight} alt="tbd"/>)}
            </section>
        </main>
    );
}

export default Login;