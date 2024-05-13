import React, { useState } from 'react';
import './Signup.css';
import { Link, useNavigate } from 'react-router-dom'; 
import Swal from 'sweetalert2'; 

import gif_img from '../../assets/images/hi_there.gif';

const Signup = () => {
    let navigate = useNavigate();

    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('');
    const [userName, setUserName] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [contactNumber, setContactNumber] = useState('');
    const [gender, setGender] = useState('');
    const [currentStep, setCurrentStep] = useState(1);

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

            let formData = new FormData();
            formData.append('email', email);
            formData.append('password', password);
            formData.append('role', role);
            formData.append('username', userName);
            formData.append('first_name', firstName);
            formData.append('last_name', lastName);
            formData.append('contact_number', contactNumber);
            formData.append('gender', gender);

            let requestOption = {
                method: 'POST',
                body: formData,
                redirect: 'follow'
            }
            

            try {
                const response = await fetch('http://0.0.0.0:8000/api/v1/auth/create-user/', requestOption);
                const responseData = await response.text();
                const jsonResponse = JSON.parse(responseData);
                console.log('success', jsonResponse);
                Swal.fire({
                icon: 'success',
                title: 'Please Verify your account via the email!',
                showConfirmButton: false,
                timer: 10000
            });
                navigate('/login');
            } catch (error) {
                console.log('Error: ', error);
            }


        }
    };

    return (
        <div className="create-user-container">
            <img src={gif_img} alt='ecom' height="200px" width="380px" className='imageClass' />
            <h3>SignUp Here</h3>
            <form onSubmit={handleSubmit} className="create-user-form">
                {currentStep === 1 && (
                    <>
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
                        <div>
                            <label>
                                <input
                                    type="checkbox"
                                    value="admin"
                                    checked={role === 'admin'}
                                    onChange={() => setRole('admin')}
                                />
                                Admin
                            </label>
                            <label>
                                <input
                                    type="checkbox"
                                    value="client"
                                    checked={role === 'client'}
                                    onChange={() => setRole('client')}
                                />
                                Client
                            </label>
                        </div>
                        <button type="submit">Next</button>
                    </>
                )}
                {currentStep === 2 && (
                    <>
                        <input
                            type="text"
                            value={userName}
                            onChange={(e) => setUserName(e.target.value)}
                            placeholder="Username"
                            required
                        />
                        <input
                            type="text"
                            value={firstName}
                            onChange={(e) => setFirstName(e.target.value)}
                            placeholder="First Name"
                            required
                        />
                        <input
                            type="text"
                            value={lastName}
                            onChange={(e) => setLastName(e.target.value)}
                            placeholder="Last Name"
                            required
                        />
                        <input
                            type="tel"
                            value={contactNumber}
                            onChange={(e) => setContactNumber(e.target.value)}
                            placeholder="Contact Number"
                            required
                        />
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
                    </>
                )}
            </form>
            <p>
                Already have an account ? {" "}
                <Link to="/login"> Sign in here</Link> 
            </p>
        </div>
    );
};

export default Signup;
