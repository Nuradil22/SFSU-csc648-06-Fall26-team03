import './Form.css';


function LoginForm( {isReturningUser, setIsReturningUser} ){
    return(
        <div className='form'>
            <div className="box form-box">
                <h1 className="box-header">Welcome Back!</h1>
                <p>Log in to continue your adventure</p>

                <div className="fields"> 
                    <input type="text" placeholder="Name" className="field"/>
                    <input type="email" placeholder="Email" className="field"/>
                    <input type="password" placeholder="Password" className="field"/>
                </div>

                <button className="form-btn" onClick={() => setIsReturningUser(!isReturningUser)}>No account? Sign up here!</button>
                <button className="form-btn">Log In</button>
            </div>
        </div>
    );
}

export default LoginForm;