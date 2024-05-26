import React from 'react';
import './Landing.css';
import { Link, useNavigate } from 'react-router-dom'; 
import gif_img from '../../assets/images/todo1.gif';

function Landing() {
  return (
    <div className="landing">
      <h1>Welcome to My ToDo App!</h1>
      <p>Start organizing your tasks today.</p>
      <div><img src={gif_img} alt='login' height="280px" width="450px" className='imageClass' /></div>
      
      <div className="button-container">
        <Link className='login_button' to="/login">
          <span className="emoji" role="img" aria-label="Emoji">😃</span> Start here
        </Link>
      </div>
    </div>
  );
}

export default Landing;
