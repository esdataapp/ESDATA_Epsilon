import React from 'react';

interface EsdataLogoProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'white' | 'color';
  className?: string;
}

const EsdataLogo: React.FC<EsdataLogoProps> = ({ 
  size = 'md', 
  variant = 'white',
  className = '' 
}) => {
  const sizeClasses = {
    sm: 'h-8',
    md: 'h-10',
    lg: 'h-12'
  };

  const filterStyle = variant === 'white' 
    ? { filter: 'brightness(0) invert(1)' } // Logo blanco
    : {}; // Logo en color original

  return (
    <div className={`flex items-center ${className}`}>
      {/* Logo oficial de Esdata */}
      <img 
        src="/logo-esdata.png" 
        alt="Esdata"
        className={`${sizeClasses[size]} w-auto object-contain`}
        style={filterStyle}
      />
    </div>
  );
};

export default EsdataLogo;
