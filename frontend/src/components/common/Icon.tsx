import React from 'react';
import { type LucideIcon } from 'lucide-react';
import { cn } from '../../utils/cn';

interface IconProps extends React.SVGProps<SVGSVGElement> {
  icon: LucideIcon;
  size?: 'sm' | 'md' | 'lg' | 'xl';
}

const Icon: React.FC<IconProps> = ({ icon: IconComponent, size = 'md', className, ...props }) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
    xl: 'h-8 w-8',
  };

  return (
    <IconComponent
      className={cn(sizes[size], className)}
      {...props}
    />
  );
};

export default Icon; 