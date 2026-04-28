import React, { useState } from 'react';

const ModelChoice = ({ options, selectedOption, onOptionSelect }) => {
  const [isOpen, setIsOpen] = useState(false);

  const toggleDropdown = () => {
    setIsOpen(!isOpen);
  };

  const handleOptionSelect = (option) => {
    onOptionSelect(option);
    setIsOpen(false);
  };

  return (
    <div className="dropdown">
      <button className="dropdown-toggle" onClick={toggleDropdown}>
        {selectedOption}
      </button>
      {isOpen && (
        <ul className="dropdown-menu show">
          {options.map((option, index) => (
            <li className="dropdown-menu-item" key={index} onClick={() => handleOptionSelect(option)}>
              {option}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default ModelChoice;