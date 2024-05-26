import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import './ChangePassword.css';
import Swal from 'sweetalert2';
import { useCookies } from 'react-cookie';

import Sidebar from '../CommonComponents/Sidebar';

const ChangePassword = () => {
    const navigate = useNavigate();
    const [oldPassword, setOldPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showOldPassword, setShowOldPassword] = useState(false);
    const [showNewPassword, setShowNewPassword] = useState(false);
    const [showConfirmPassword, setShowConfirmPassword] = useState(false);
    const [id, , removeId] = useCookies(['id']);
    const [isAdmin, , removeIsAdmin] = useCookies(['is_admin']);

    const handleSubmit = async (e) => {
        e.preventDefault();
        const errors = {};

        if (newPassword !== confirmPassword) {
            errors.newPassword = "New Password and Confirm Password do not match";
        }
        if (!newPassword.trim()) {
            errors.newPassword = "Password is required";
        } else if (newPassword.trim().length < 4) {
            errors.newPassword = "Password must be at least 4 characters long";
        }

        if (!oldPassword.trim()) {
            errors.oldPassword = "Password is required";
        } else if (oldPassword.trim().length < 4) {
            errors.oldPassword = "Password must be at least 4 characters long";
        }

        if (Object.keys(errors).length > 0) {
            console.log(errors);
            return;
        }

        let formData = new FormData();
        formData.append('old_password', oldPassword);
        formData.append('new_password', newPassword);

        let requestOption = {
            method: 'POST',
            body: formData,
            redirect: 'follow',
            credentials: "include",
        }

        try {
            const response = await fetch('/api/v1/auth/change-password/', requestOption);
            console.log('success !!!');
            Swal.fire({
                icon: 'success',
                title: 'Successfully changed the password!',
                showConfirmButton: false,
                timer: 1500
            });
            removeId('id');
            removeIsAdmin('is_admin')
            navigate('/login');
        } catch (error) {
            console.log('Error: ', error);
        }
    };

    return (
        <>
            <div className="change-container">
                <h2>Change Password</h2>
                <form onSubmit={handleSubmit} className="change-form">
                    <div className="password-input">
                        <input
                            type={showOldPassword ? "text" : "password"}
                            value={oldPassword}
                            onChange={(e) => setOldPassword(e.target.value)}
                            placeholder="Current Password"
                            required
                        />
                        <i className={`fas ${showOldPassword ? "fa-eye" : "fa-eye-slash"} password-icon`}
                           onClick={() => setShowOldPassword(!showOldPassword)}></i>
                    </div>
                    <div className="password-input">
                        <input
                            type={showNewPassword ? "text" : "password"}
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            placeholder="New Password"
                            required
                        />
                        <i className={`fas ${showNewPassword ? "fa-eye" : "fa-eye-slash"} password-icon`}
                           onClick={() => setShowNewPassword(!showNewPassword)}></i>
                    </div>
                    <div className="password-input">
                        <input
                            type={showConfirmPassword ? "text" : "password"}
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            placeholder="Confirm New Password"
                            required
                        />
                        <i className={`fas ${showConfirmPassword ? "fa-eye" : "fa-eye-slash"} password-icon`}
                           onClick={() => setShowConfirmPassword(!showConfirmPassword)}></i>
                    </div>
                    <button type="submit">Change Password</button>
                </form>
            </div>
        </>
    );
};

export default ChangePassword;
