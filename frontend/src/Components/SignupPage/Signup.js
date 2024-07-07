import React, { useState } from 'react';
import './Signup.css';
import { Link, useNavigate } from 'react-router-dom';
import Swal from 'sweetalert2';

import gif_img from '../../assets/images/hi_there.gif';


const LoaderModal = () => (
    <div className="modal">
        <div className="modal-content">
            <div className="loader"></div>
            <p className="loader_text">Loading...</p>
        </div>
    </div>
);

const Signup = () => {
    let navigate = useNavigate();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [userName, setUserName] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [contactNumber, setContactNumber] = useState('');
    const [gender, setGender] = useState('');
    const [currentStep, setCurrentStep] = useState(1);
    const [isLoading, setIsLoading] = useState(false);

    const isValidBangladeshiPhoneNumber = (phoneNumber) => {
        const regex = /^(?:\+?88|0088)?01[3-9]\d{8}$/;
        return regex.test(phoneNumber);
    };

    // const isValidEmail = (email) => {
    //     const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    //     return regex.test(email);
    // };

    const isValidPassword = (password) => {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return password.length >= minLength && hasUpperCase && hasLowerCase && hasNumber && hasSpecialChar;
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        const errors = {};

        if (currentStep === 1) {
            setCurrentStep(2);
        } else {
            if (Object.keys(errors).length > 0) {
                console.log(errors);
                return;
            }

            // if (!isValidEmail(email)) {
            //     Swal.fire({
            //         icon: 'error',
            //         title: 'Invalid Email',
            //         text: 'Please enter a valid email address',
            //     });
            //     return;
            // }

            if (!isValidPassword(password)) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Password',
                    text: 'Password must be at least 8 characters long and include an uppercase letter, a lowercase letter, a number, and a special character',
                });
                return;
            }

            if (!isValidBangladeshiPhoneNumber(contactNumber)) {
                Swal.fire({
                    icon: 'error',
                    title: 'Invalid Phone Number',
                    text: 'Please enter a valid Bangladeshi phone number',
                });
                return;
            }

            const data = {
                email: email,
                password: password,
                role: 'user',
                username: userName,
                first_name: firstName,
                last_name: lastName,
                contact_number: contactNumber,
                gender: gender,
            };

            let requestOption = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
                redirect: 'follow'
            };

            setIsLoading(true);

            try {
                const response = await fetch('/api/v1/auth/create-user/', requestOption);
                if (!response.ok) {
                    const errorData = await response.json();
                    let errorMessage = '';

                    if (errorData.detail) {
                        if (Array.isArray(errorData.detail)) {
                            errorMessage = errorData.detail.map(detail => detail.msg).join(' ');
                        } else {
                            errorMessage = errorData.detail;
                        }
                    } else {
                        errorMessage = 'An unknown error occurred';
                    }

                    throw new Error(errorMessage);
                }

                const jsonResponse = await response.json();
                console.log('success', jsonResponse);
                Swal.fire({
                    icon: 'success',
                    title: 'Please Verify your account via the email!',
                    showConfirmButton: false,
                    timer: 4000
                });
                navigate('/login');
            } catch (error) {
                console.log('Error: ', error);
                Swal.fire({
                    icon: 'error',
                    title: 'Error',
                    text: error.message || 'Something went wrong!',
                });

            } finally {
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="create-user-container">
            <img src={gif_img} alt='ecom' height="200px" width="380px" className='imageClass' />
            <h3>SignUp Here</h3>
            {isLoading && <LoaderModal />}
            <form onSubmit={handleSubmit} className="create-user-form">

                    <input
                        className="user-create-input"
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Email"
                        required
                    />
                    <input
                        className="user-create-input"
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                        required
                    />
                    <input
                        className="user-create-input"
                        type="text"
                        value={userName}
                        onChange={(e) => setUserName(e.target.value)}
                        placeholder="Username"
                        required
                    />
                    <input
                        className="user-create-input"
                        type="text"
                        value={firstName}
                        onChange={(e) => setFirstName(e.target.value)}
                        placeholder="First Name"
                        required
                    />
                    <input
                        className="user-create-input"
                        type="text"
                        value={lastName}
                        onChange={(e) => setLastName(e.target.value)}
                        placeholder="Last Name"
                        required
                    />
                    <input
                        className="user-create-input"
                        type="tel"
                        value={contactNumber}
                        onChange={(e) => setContactNumber(e.target.value)}
                        placeholder="Contact Number"
                        required
                    />
                    <hr />
                    <div>
                        <label>
                            <input
                                type="radio"
                                value="male"
                                checked={gender === 'male'}
                                onChange={() => setGender('male')}
                            />
                            Male
                        </label>
                        <label>
                            <input
                                type="radio"
                                value="female"
                                checked={gender === 'female'}
                                onChange={() => setGender('female')}
                            />
                            Female
                        </label>
                    </div>
                    <button type="submit">Create User</button>

            </form>
            <p>
                Already have an account ? {" "}
                <Link to="/login"> Sign in here</Link>
            </p>
        </div>
    );
};

export default Signup;
