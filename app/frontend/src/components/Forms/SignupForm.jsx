import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css';
import { signup } from '../../lib/api';

function SignupForm({ isReturningUser, setIsReturningUser }) {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const navigate = useNavigate();

    async function handleSubmit(e) {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);

        try {
            const data = await signup({ name, email, password });
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('user', JSON.stringify(data.user));
            navigate('/');
        } catch (err) {
            setError(err.message);
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <form className='form' onSubmit={handleSubmit}>
            <div className="box form-box">
                <h1 className="box-header">Create an Account:</h1>
                <p>Your Journey Begins Here!</p>

                <div className="fields">
                    <input
                        type="text"
                        placeholder="Name"
                        className="field"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                    <input
                        type="email"
                        placeholder="Email"
                        className="field"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                    />
                    <input
                        type="password"
                        placeholder="Password"
                        className="field"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                    />
                </div>

                {error && <p className="form-error">{error}</p>}

                <button type="button" className="form-btn" onClick={() => setIsReturningUser(!isReturningUser)}>
                    Already have an account?
                </button>
                <button type="submit" className="form-btn" disabled={isSubmitting}>
                    {isSubmitting ? 'Signing Up...' : 'Sign Up'}
                </button>
            </div>
        </form>
    );
}

export default SignupForm;
