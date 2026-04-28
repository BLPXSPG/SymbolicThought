import React from 'react';
import { useNavigate } from 'react-router-dom';

const NavigationButton = ({ path, name, message, children }) => {
  const navigate = useNavigate();

  const handleClick = () => {
    const dataToPass = {
      taskValue: message
    };
    navigate(path, { state: dataToPass });
  };
  return (
    <button className='Homepage-button' onClick={handleClick}> {name} </button>
  );
};

export default NavigationButton;