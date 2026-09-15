import './Form.css';

function SignupForm( {isReturningUser, setIsReturningUser} ){
    return(
        <div className='form'>
            <div className="box form-box">
                <h1 className="box-header">Create an Account:</h1>
                <p>Your Journey Begins Here!</p>

                <div className="fields"> 
                    <input type="text" placeholder="Name" className="field"/>
                    <input type="email" placeholder="Email" className="field"/>
                    <input type="password" placeholder="Password" className="field"/>
                </div>

                <button className="form-btn" onClick={() => setIsReturningUser(!isReturningUser)}>Already have an account?</button>
                <button className="form-btn">Sign Up</button>
            </div>
        </div>
    );
}

export default SignupForm;