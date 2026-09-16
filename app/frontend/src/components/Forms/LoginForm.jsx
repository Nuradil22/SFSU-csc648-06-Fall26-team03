import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './Form.css';
import { login } from '../../lib/api';

function LoginForm({ isReturningUser, setIsReturningUser }) {
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
            const data = await login({ email, password });
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
                <h1 className="box-header">Welcome Back!</h1>
                <p>Log in to continue your adventure</p>

                <div className="fields">
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
                    No account? Sign up here!
                </button>
                <button type="submit" className="form-btn" disabled={isSubmitting}>
                    {isSubmitting ? 'Logging In...' : 'Log In'}
                </button>
            </div>
        </form>
    );
}

export default LoginForm;
