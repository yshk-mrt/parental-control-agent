import React, { useState } from 'react';
import { Card, CardHeader, CardContent } from '../common/Card';
import Button from '../common/Button';
import Icon from '../common/Icon';
import { 
  Compass, 
  Clock, 
  MessageCircle, 
  Shield, 
  AlertTriangle, 
  CheckCircle, 
  Star, 
  Trophy,
  Book,
  Lightbulb,
  Target,
  TrendingUp
} from 'lucide-react';

interface LearningActivity {
  id: string;
  date: string;
  question: string;
  answer: string;
  category: string;
  achievement?: string;
  parentNote?: string;
}

interface InterestData {
  keyword: string;
  level: 'high' | 'medium' | 'low';
  color: string;
}

interface ExploredField {
  name: string;
  progress: number;
  color: string;
}

const LearningDashboard: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState<'overview' | 'timeline' | 'interests' | 'communication'>('overview');

  // Mock data - in real implementation, this would come from backend
  const interestKeywords: InterestData[] = [
    { keyword: 'Dinosaurs', level: 'high', color: 'text-purple-600' },
    { keyword: 'Space', level: 'high', color: 'text-blue-600' },
    { keyword: 'Why', level: 'medium', color: 'text-green-600' },
    { keyword: 'Programming', level: 'medium', color: 'text-indigo-600' },
    { keyword: 'Art', level: 'low', color: 'text-pink-600' },
    { keyword: 'Animals', level: 'low', color: 'text-orange-600' },
    { keyword: 'How', level: 'low', color: 'text-teal-600' },
  ];

  const exploredFields: ExploredField[] = [
    { name: 'Science', progress: 85, color: 'bg-green-500' },
    { name: 'History', progress: 45, color: 'bg-yellow-500' },
    { name: 'Arts', progress: 30, color: 'bg-pink-500' },
  ];

  const learningActivities: LearningActivity[] = [
    {
      id: '1',
      date: 'July 12',
      question: 'Why do T-Rex have short arms?',
      answer: "It's believed that the arms became small and light to support the large head and jaw.",
      category: 'Science',
      parentNote: "The arms weren't used for hunting but may have helped with getting up from the ground."
    },
    {
      id: '2',
      date: 'July 11',
      question: 'Why are rainbows 7 colors?',
      answer: 'Sunlight splits into 7 colors when it passes through water droplets in the air, just like a prism.',
      category: 'Science',
      achievement: 'Understood "light refraction"!'
    }
  ];

  const weeklyHighlights = {
    mainInterest: 'dinosaurs',
    suggestion: 'How about reading a dinosaur encyclopedia together this weekend?',
    deepDiveQuestions: [
      "What's your favorite dinosaur?",
      "If you could meet a dinosaur, what would you want to do?"
    ]
  };

  const safetyAlert = {
    level: 'attention',
    message: 'This week, we detected some concerning behavior patterns. Your child asked about inappropriate topics multiple times. Please review the content and discuss appropriate boundaries with your child.',
    hasApprovalPending: true
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-blue-600">User's Learning Dashboard</h1>
          <p className="text-gray-600">Track your child's curiosity and growth journey.</p>
        </div>
        <div className="flex gap-2">
          <Button 
            variant={selectedTab === 'overview' ? 'primary' : 'outline'} 
            size="sm"
            onClick={() => setSelectedTab('overview')}
          >
            Overview
          </Button>
          <Button 
            variant={selectedTab === 'timeline' ? 'primary' : 'outline'} 
            size="sm"
            onClick={() => setSelectedTab('timeline')}
          >
            Timeline
          </Button>
          <Button 
            variant={selectedTab === 'interests' ? 'primary' : 'outline'} 
            size="sm"
            onClick={() => setSelectedTab('interests')}
          >
            Interests
          </Button>
          <Button 
            variant={selectedTab === 'communication' ? 'primary' : 'outline'} 
            size="sm"
            onClick={() => setSelectedTab('communication')}
          >
            Communication
          </Button>
        </div>
      </div>

      {/* Safety & Security Report */}
      <Card className="border-l-4 border-l-red-500">
        <CardHeader>
          <div className="flex items-center space-x-2">
            <Icon icon={AlertTriangle} className="w-5 h-5 text-red-500" />
            <h2 className="text-lg font-semibold">Safety & Security Report</h2>
          </div>
        </CardHeader>
        <CardContent>
          <div className="bg-red-50 rounded-lg p-4 mb-4">
            <div className="flex items-start space-x-3">
              <Icon icon={Shield} className="w-5 h-5 text-red-500 mt-1" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-500 mb-1">Attention Required!</h3>
                <p className="text-sm text-gray-600 mb-3">
                  {safetyAlert.message}
                </p>
                {safetyAlert.hasApprovalPending && (
                  <Button variant="primary" size="sm" className="flex items-center gap-2">
                    <Icon icon={CheckCircle} className="w-4 h-4" />
                    Approve After Review
                  </Button>
                )}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content based on selected tab */}
      {selectedTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Interest Compass */}
          <Card className="lg:col-span-2 card-hover">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Icon icon={Compass} className="w-5 h-5 text-blue-600" />
                <h2 className="text-lg font-semibold">Interest Compass</h2>
                <Icon icon={Lightbulb} className="w-4 h-4 text-yellow-500" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Interest Keywords */}
                <div>
                  <h3 className="font-medium mb-3">Interest Keywords</h3>
                  <div className="interest-cloud">
                    {interestKeywords.map((interest, index) => (
                      <span
                        key={index}
                        className={`interest-keyword ${interest.color} bg-current/10`}
                      >
                        {interest.keyword}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Explored Fields */}
                <div>
                  <h3 className="font-medium mb-3">Explored Fields</h3>
                  <div className="space-y-3">
                    {exploredFields.map((field, index) => (
                      <div key={index}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="font-medium">{field.name}</span>
                          <span className="text-muted-foreground">{field.progress}%</span>
                        </div>
                        <div className="w-full bg-muted rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${field.color} progress-bar`}
                            style={{ width: `${field.progress}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Communication Supporter */}
          <Card className="card-hover">
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Icon icon={MessageCircle} className="w-5 h-5 text-teal-600" />
                <h2 className="text-lg font-semibold">Communication Supporter</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <h3 className="font-medium mb-2 text-primary">This Week's Highlights</h3>
                  <p className="text-sm text-muted-foreground">
                    This week, your child was particularly fascinated by "{weeklyHighlights.mainInterest}". {weeklyHighlights.suggestion}
                  </p>
                </div>

                <div>
                  <h3 className="font-medium mb-2 text-destructive">Deep Dive Questions</h3>
                  <ul className="space-y-1">
                    {weeklyHighlights.deepDiveQuestions.map((question, index) => (
                      <li key={index} className="text-sm text-muted-foreground flex items-start">
                        <span className="w-2 h-2 bg-destructive rounded-full mt-2 mr-2 flex-shrink-0" />
                        {question}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {selectedTab === 'timeline' && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Icon icon={Clock} className="w-5 h-5 text-success" />
              <h2 className="text-lg font-semibold">Learning Timeline</h2>
              <Icon icon={TrendingUp} className="w-4 h-4 text-success" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {learningActivities.map((activity) => (
                <div key={activity.id} className="timeline-item border-l-4 border-l-primary pl-4 pb-4">
                  <div className="flex items-center space-x-2 mb-2">
                    <Icon icon={Book} className="w-4 h-4 text-primary" />
                    <span className="text-sm font-medium text-muted-foreground">{activity.date}</span>
                    {activity.achievement && (
                      <div className="flex items-center space-x-1">
                        <Icon icon={Trophy} className="w-4 h-4 text-accent" />
                        <span className="text-xs text-accent font-medium">Achievement!</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="mb-2">
                    <h3 className="font-medium mb-1">Q: {activity.question}</h3>
                    <p className="text-sm text-muted-foreground">A: {activity.answer}</p>
                  </div>

                  {activity.achievement && (
                    <div className="bg-accent/10 rounded-lg p-3 mb-2">
                      <div className="flex items-center space-x-2">
                        <Icon icon={Star} className="w-4 h-4 text-accent" />
                        <span className="text-sm font-medium text-accent">Achievement! {activity.achievement}</span>
                      </div>
                    </div>
                  )}

                  {activity.parentNote && (
                    <div className="bg-success/10 rounded-lg p-3">
                      <div className="flex items-start space-x-2">
                        <Icon icon={MessageCircle} className="w-4 h-4 text-success mt-0.5" />
                        <div>
                          <span className="text-xs font-medium text-success block">For Parents:</span>
                          <span className="text-sm text-muted-foreground">{activity.parentNote}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {selectedTab === 'interests' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Icon icon={Target} className="w-5 h-5 text-primary" />
                <h2 className="text-lg font-semibold">Interest Analysis</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {interestKeywords.map((interest, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                    <span className={`font-medium ${interest.color}`}>{interest.keyword}</span>
                    <div className="flex items-center space-x-2">
                      <div className={`w-2 h-2 rounded-full ${interest.color.replace('text-', 'bg-')}`} />
                      <span className="text-sm text-muted-foreground capitalize">{interest.level}</span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center space-x-2">
                <Icon icon={TrendingUp} className="w-5 h-5 text-success" />
                <h2 className="text-lg font-semibold">Learning Progress</h2>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {exploredFields.map((field, index) => (
                  <div key={index} className="space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="font-medium">{field.name}</span>
                      <span className="text-sm text-muted-foreground">{field.progress}%</span>
                    </div>
                    <div className="w-full bg-muted rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full ${field.color} transition-all duration-300`}
                        style={{ width: `${field.progress}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {selectedTab === 'communication' && (
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <Icon icon={MessageCircle} className="w-5 h-5 text-secondary" />
              <h2 className="text-lg font-semibold">Communication Tools</h2>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-3">Conversation Starters</h3>
                <div className="space-y-2">
                  {weeklyHighlights.deepDiveQuestions.map((question, index) => (
                    <div key={index} className="p-3 bg-secondary/10 rounded-lg">
                      <p className="text-sm">{question}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-medium mb-3">Weekly Summary</h3>
                <div className="p-4 bg-primary/10 rounded-lg">
                  <p className="text-sm text-muted-foreground">
                    Your child showed strong interest in {weeklyHighlights.mainInterest} this week. 
                    Consider exploring related topics like paleontology or natural history museums.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LearningDashboard; 