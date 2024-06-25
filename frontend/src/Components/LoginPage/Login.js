import React, { useState } from 'react';
import './Login.css';
import { Link, useNavigate } from 'react-router-dom'; 
import { useCookies } from 'react-cookie';
import Swal from 'sweetalert2'; 




import gif_img from '../../assets/images/hi_there.gif';

const Login = () => {

    let navigate = useNavigate();


    const [id, setId] = useCookies(['id']);
    const [isAdmin, setIsAdmin] = useCookies(['is_admin']);

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
    
        const errors = {};

        if (!email.trim()) {
            errors.email = "Email Address is required";
        } else if (!/\S+@\S+\.\S+/.test(email)) {
            errors.email = "Invalid email format";
        }

        if (!password.trim()) {
            errors.password = "Password is required";
        } else if (password.trim().length < 4) {
            errors.password = "Password must be at least 4 characters long";
        }
 
        if (Object.keys(errors).length > 0) {
            console.log(errors);
            return;
        }

        const data = {
            email: email,
            password: password
        };

        let requestOption = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            redirect: 'follow',
            credentials: "include", 
        }
        

        try {
            const response = await fetch('/api/v1/auth/login/', requestOption);
            if (!response.ok) {
                const errorResponse = await response.json();
                throw new Error(errorResponse.detail);
            }

            const jsonResponse = await response.json();
            setId('id', jsonResponse.id);
            setIsAdmin('is_admin', jsonResponse.is_admin);
            Swal.fire({
                icon: 'success',
                title: 'Login successful!',
                showConfirmButton: false,
                timer: 1500
            });
            navigate('/home');
        } catch (error) {
            console.log('Error: ', error);

            let errorMessage = 'Something went wrong!';

            if (error.message === 'Invalid email or password') {
                errorMessage = 'Invalid email or password';
            } else if (error.message === 'User not found') {
                errorMessage = 'User not found';
            } else if (error.message === 'User is not active') {
                errorMessage = 'User is not active';
            } else {
                errorMessage = error.message;
            }

            Swal.fire({
                icon: 'error',
                title: 'Login Failed',
                text: errorMessage,
            });
        }
    };


    return (
        <div className="login-user-container">
            <img src={gif_img} alt='login' height="280px" width="450px" className='imageClass' />
            <h2>Login Here</h2>
            <form onSubmit={handleSubmit} className="login-user-form">
                <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                />
                <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                />
                <button type="submit">Login</button>
            </form>
            <p>
                Don't have an account? {" "}
                <Link to="/sign-up"> Sign up here</Link>
            </p>

            <p>
                <Link className='forget-password' to="/forget-password">Forget Password ?</Link>
            </p>

        </div>
    );
};

export default Login;
