import React, { useState, useEffect } from 'react';
import './Home.css';
import Sidebar from '../CommonComponents/Sidebar';
import { Link, useNavigate } from 'react-router-dom';

import { useCookies } from 'react-cookie';

import gif_img_female from '../../assets/images/female.gif';
import gif_img_male from '../../assets/images/male.gif';
import Swal from 'sweetalert2';

const Home = () => {

    const navigate = useNavigate();


    return (
        <>
            <Sidebar />
            <div className="profile-container">
                
            </div>

        </>
    );
};

export default Home;
