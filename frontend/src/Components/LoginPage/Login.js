import React, { useState } from 'react';
import './Login.css';
import { Link, useNavigate } from 'react-router-dom'; 
// import { useCookies } from 'react-cookie';
import Swal from 'sweetalert2'; 




import gif_img from '../../assets/images/hi_there.gif';

const Login = () => {

    let navigate = useNavigate();


    // const [role, setRole] = useCookies(['role']);
    // const [token] = useCookies(['myToken']);

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

        let formData = new FormData();
        formData.append('email', email);
        formData.append('password', password)

        let requestOption = {
            method: 'POST',
            body: formData,
            redirect: 'follow',
            credentials: "include", 
        }
        

        try {
            const response = await fetch('http://0.0.0.0:8000/api/v1/auth/login/', requestOption);
            const responseData = await response.text();
            const cookie = response.headers.get('Set-Cookie');
            // console.log(cookie);
            const jsonResponse = JSON.parse(responseData);
            console.log('success !!!');
            
            // setRole('role', jsonResponse.role);
            // setRole('myToken', jsonResponse.token);
            Swal.fire({
                icon: 'success',
                title: 'Login successful!',
                showConfirmButton: false,
                timer: 1500
            });
            navigate('/');
        } catch (error) {
            console.log('Error: ', error);
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
        </div>
    );
};

export default Login;
