import React, { useState } from 'react';
import { Search, Link2, Tag, BarChart3, Shield, Users, ChevronDown, ChevronRight, Play, Copy, Check, type LucideIcon } from 'lucide-react';

interface RequestBody {
  [key: string]: string;
}

interface Endpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
  auth: 'None' | 'Required' | 'Optional' | 'Refresh Token';
  params?: string[];
  request?: RequestBody;
  response?: string;
}

interface RouteCategory {
  category: string;
  name: string;
  icon: LucideIcon;
  color: 'blue' | 'purple' | 'green' | 'orange' | 'indigo';
  endpoints: Endpoint[];
}

interface RequestDataState {
  [key: string]: {
    [field: string]: string | number | boolean;
  };
}

interface ResponseData {
  status: number | string;
  statusText: string;
  data: any;
}

interface ResponsesState {
  [key: string]: ResponseData;
}

interface BooleanState {
  [key: string]: boolean;
}

const BASE_URL = "http://localhost:8000"

const APIRoutesExplorer: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedRoutes, setExpandedRoutes] = useState<BooleanState>({});
  const [testingRoute, setTestingRoute] = useState<BooleanState>({});
  const [requestData, setRequestData] = useState<RequestDataState>({});
  const [responses, setResponses] = useState<ResponsesState>({});
  const [loading, setLoading] = useState<BooleanState>({});
  const [copiedResponse, setCopiedResponse] = useState<string | null>(null);

  const routes: RouteCategory[] = [
    {
      category: 'shorten',
      name: 'URL Shortening',
      icon: Link2,
      color: 'blue',
      endpoints: [
        {
          method: 'POST',
          path: '/api/v1/',
          description: 'Create a shortened URL',
          auth: 'Optional',
          request: { url: 'string', title: 'string?', descr: 'string?', is_favorite: 'boolean?' },
          response: 'URLResponse'
        },
        {
          method: 'GET',
          path: '/api/v1/{short_code}',
          description: 'Redirect to original URL from short code',
          auth: 'None',
          params: ['short_code']
        },
        {
          method: 'GET',
          path: '/api/v1/{short_code}/stats',
          description: 'Get statistics for a shortened URL',
          auth: 'None',
          params: ['short_code'],
          response: 'UrlStats'
        }
      ]
    },
    {
      category: 'tags',
      name: 'Tags Management',
      icon: Tag,
      color: 'purple',
      endpoints: [
        {
          method: 'GET',
          path: '/api/v1/user/tags/',
          description: 'Get user tags with pagination',
          auth: 'Required',
          params: ['limit?', 'offset?'],
          response: 'Pagination<UrlTag>'
        },
        {
          method: 'POST',
          path: '/api/v1/user/tags/',
          description: 'Create a new tag',
          auth: 'Required',
          request: { name: 'string', color: 'string?', descr: 'string?' },
          response: 'UrlTag'
        },
        {
          method: 'PUT',
          path: '/api/v1/user/tags/',
          description: 'Update an existing tag',
          auth: 'Required',
          request: { id: 'integer', name: 'string?', color: 'string?', descr: 'string?' }
        },
        {
          method: 'DELETE',
          path: '/api/v1/user/tags/',
          description: 'Delete a tag',
          auth: 'Required',
          request: { id: 'integer' }
        },
        {
          method: 'GET',
          path: '/api/v1/user/tags/relations',
          description: 'Get URLs from a specific tag',
          auth: 'Required',
          params: ['limit?', 'offset?'],
          request: { id: 'integer' },
          response: 'Pagination<URLResponse>'
        },
        {
          method: 'POST',
          path: '/api/v1/user/tags/relations',
          description: 'Associate a tag with a URL',
          auth: 'Required',
          request: { url_id: 'integer', tag_id: 'integer' }
        },
        {
          method: 'DELETE',
          path: '/api/v1/user/tags/relations',
          description: 'Remove tag association from URL',
          auth: 'Required',
          request: { url_id: 'integer', tag_id: 'integer' }
        },
        {
          method: 'DELETE',
          path: '/api/v1/user/tags/relations/clear',
          description: 'Clear all URLs from a tag',
          auth: 'Required',
          request: { id: 'integer' }
        }
      ]
    },
    {
      category: 'dashboard',
      name: 'Dashboard Analytics',
      icon: BarChart3,
      color: 'green',
      endpoints: [
        {
          method: 'GET',
          path: '/api/v1/dashboard/data',
          description: 'Get comprehensive dashboard statistics',
          auth: 'None',
          response: 'Dashboard'
        },
        {
          method: 'PUT',
          path: '/api/v1/dashboard/refresh',
          description: 'Refresh dashboard statistics',
          auth: 'Required',
          response: 'Dashboard'
        }
      ]
    },
    {
      category: 'user',
      name: 'User Management',
      icon: Users,
      color: 'orange',
      endpoints: [
        {
          method: 'GET',
          path: '/api/v1/user/url',
          description: 'Get user URLs with pagination',
          auth: 'Required',
          params: ['limit?', 'offset?'],
          response: 'Pagination<UserURLResponse>'
        },
        {
          method: 'DELETE',
          path: '/api/v1/user/url',
          description: 'Delete a user URL',
          auth: 'Required',
          request: { id: 'integer' }
        },
        {
          method: 'PUT',
          path: '/api/v1/user/url/favorite',
          description: 'Set URL as favorite',
          auth: 'Required',
          request: { url_id: 'integer', is_favorite: 'boolean' }
        }
      ]
    },
    {
      category: 'auth',
      name: 'Authentication',
      icon: Shield,
      color: 'indigo',
      endpoints: [
        {
          method: 'GET',
          path: '/api/v1/auth/me',
          description: 'Get current user information',
          auth: 'Required',
          response: 'User'
        },
        {
          method: 'POST',
          path: '/api/v1/auth/login',
          description: 'Authenticate user and create session',
          auth: 'None',
          request: { email: 'string', password: 'string' },
          response: 'User'
        },
        {
          method: 'POST',
          path: '/api/v1/auth/signup',
          description: 'Register new user account',
          auth: 'None',
          request: { email: 'string', password: 'string' }
        },
        {
          method: 'GET',
          path: '/api/v1/auth/sessions',
          description: 'Get active user sessions',
          auth: 'Required',
          params: ['limit?', 'offset?'],
          response: 'Pagination<UserSession>'
        },
        {
          method: 'POST',
          path: '/api/v1/auth/refresh',
          description: 'Refresh authentication token',
          auth: 'Refresh Token',
          response: 'User'
        },
        {
          method: 'POST',
          path: '/api/v1/auth/logout',
          description: 'Logout from current session',
          auth: 'Refresh Token'
        },
        {
          method: 'POST',
          path: '/api/v1/auth/logout/all',
          description: 'Logout from all sessions',
          auth: 'Required'
        }
      ]
    }
  ];

  const toggleRoute = (categoryIndex: number, endpointIndex: number): void => {
    const key = `${categoryIndex}-${endpointIndex}`;
    setExpandedRoutes(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const toggleTesting = (categoryIndex: number, endpointIndex: number): void => {
    const key = `${categoryIndex}-${endpointIndex}`;
    setTestingRoute(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  const updateRequestData = (key: string, field: string, value: string | number | boolean): void => {
    setRequestData(prev => ({
      ...prev,
      [key]: {
        ...(prev[key] || {}),
        [field]: value
      }
    }));
  };

  const handleTest = async (categoryIndex: number, endpointIndex: number, endpoint: Endpoint): Promise<void> => {
    const key = `${categoryIndex}-${endpointIndex}`;
    setLoading(prev => ({ ...prev, [key]: true }));

    try {
      const data = requestData[key] || {};
      let url = endpoint.path;
      
      // Replace path parameters
      if (endpoint.params) {
        endpoint.params.forEach(param => {
          const paramName = param.replace('?', '');
          if (data[paramName]) {
            url = url.replace(`{${paramName}}`, String(data[paramName]));
          }
        });
      }

      // Build query string for GET requests with query params
      if (endpoint.method === 'GET' && endpoint.params) {
        const queryParams = endpoint.params
          .filter(p => p.includes('?') && data[p.replace('?', '')])
          .map(p => {
            const paramName = p.replace('?', '');
            return `${paramName}=${encodeURIComponent(String(data[paramName]))}`;
          })
          .join('&');
        
        if (queryParams) {
          url += '?' + queryParams;
        }
      }

      const options: RequestInit = {
        method: endpoint.method,
        headers: {
          'Content-Type': 'application/json',
        }
      };

      // Add body for POST, PUT, DELETE requests
      if (['POST', 'PUT', 'DELETE'].includes(endpoint.method) && endpoint.request) {
        const bodyData: { [key: string]: any } = {};
        Object.keys(endpoint.request).forEach(field => {
          if (data[field] !== undefined && data[field] !== '') {
            bodyData[field] = data[field];
          }
        });
        options.body = JSON.stringify(bodyData);
      }

      // Add auth token if required
      if (data.access_token) {
        options.headers = {
          ...options.headers,
          'Cookie': `access_token=${data.access_token}`
        };
      }

      const response = await fetch(BASE_URL + url, options);
      const responseData = await response.json();

      setResponses(prev => ({
        ...prev,
        [key]: {
          status: response.status,
          statusText: response.statusText,
          data: responseData
        }
      }));
    } catch (error) {
      setResponses(prev => ({
        ...prev,
        [key]: {
          status: 'Error',
          statusText: error instanceof Error ? error.message : 'Unknown error',
          data: null
        }
      }));
    } finally {
      setLoading(prev => ({ ...prev, [key]: false }));
    }
  };

  const copyResponse = (key: string): void => {
    const response = responses[key];
    if (response) {
      navigator.clipboard.writeText(JSON.stringify(response.data, null, 2));
      setCopiedResponse(key);
      setTimeout(() => setCopiedResponse(null), 2000);
    }
  };

  const getMethodColor = (method: string): string => {
    const colors: { [key: string]: string } = {
      GET: 'bg-green-600',
      POST: 'bg-blue-600',
      PUT: 'bg-yellow-600',
      DELETE: 'bg-red-600'
    };
    return colors[method] || 'bg-gray-600';
  };

  const getCategoryColor = (color: string): string => {
    const colors: { [key: string]: string } = {
      blue: 'bg-blue-600',
      purple: 'bg-purple-600',
      green: 'bg-green-600',
      orange: 'bg-orange-600',
      indigo: 'bg-indigo-600'
    };
    return colors[color] || 'bg-gray-600';
  };

  const filteredRoutes = routes.filter(category => {
    if (selectedCategory !== 'all' && category.category !== selectedCategory) return false;
    if (!searchTerm) return true;
    
    const searchLower = searchTerm.toLowerCase();
    return category.name.toLowerCase().includes(searchLower) ||
           category.endpoints.some(ep => 
             ep.path.toLowerCase().includes(searchLower) ||
             ep.description.toLowerCase().includes(searchLower)
           );
  });

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">

        {/* Search and Filter */}
        <div className="mb-8 space-y-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Search endpoints..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-12 pr-4 py-4 bg-white border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setSelectedCategory('all')}
              className={`px-4 py-2 rounded-lg transition-all ${
                selectedCategory === 'all'
                  ? 'bg-gray-900 text-white'
                  : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'
              }`}
            >
              All
            </button>
            {routes.map((category) => {
              const Icon = category.icon;
              return (
                <button
                  key={category.category}
                  onClick={() => setSelectedCategory(category.category)}
                  className={`px-4 py-2 rounded-lg transition-all flex items-center gap-2 ${
                    selectedCategory === category.category
                      ? `${getCategoryColor(category.color)} text-white`
                      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  {category.name}
                </button>
              );
            })}
          </div>
        </div>

        {/* Routes */}
        <div className="space-y-6">
          {filteredRoutes.map((category, categoryIndex) => {
            const Icon = category.icon;
            return (
              <div key={category.category} className="bg-white rounded-lg overflow-hidden border border-gray-200 shadow-sm">
                <div className={`${getCategoryColor(category.color)} p-6`}>
                  <div className="flex items-center gap-3 text-white">
                    <Icon className="w-8 h-8" />
                    <div>
                      <h2 className="text-2xl font-bold">{category.name}</h2>
                      <p className="text-white/90 text-sm">{category.endpoints.length} endpoints</p>
                    </div>
                  </div>
                </div>

                <div className="divide-y divide-gray-200">
                  {category.endpoints.map((endpoint, endpointIndex) => {
                    const key = `${categoryIndex}-${endpointIndex}`;
                    const isExpanded = expandedRoutes[key];
                    const isTesting = testingRoute[key];
                    const isLoading = loading[key];
                    const response = responses[key];

                    return (
                      <div key={endpointIndex} className="hover:bg-gray-50 transition-colors">
                        <button
                          onClick={() => toggleRoute(categoryIndex, endpointIndex)}
                          className="w-full p-6 text-left"
                        >
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-3 flex-wrap">
                                <span className={`${getMethodColor(endpoint.method)} text-white px-3 py-1 rounded-lg text-sm font-bold`}>
                                  {endpoint.method}
                                </span>
                                <code className="text-blue-600 font-mono text-sm bg-blue-50 px-3 py-1 rounded border border-blue-200">
                                  {endpoint.path}
                                </code>
                                <span className={`text-xs px-2 py-1 rounded ${
                                  endpoint.auth === 'Required' ? 'bg-red-100 text-red-700 border border-red-200' :
                                  endpoint.auth === 'Optional' ? 'bg-yellow-100 text-yellow-700 border border-yellow-200' :
                                  endpoint.auth === 'Refresh Token' ? 'bg-purple-100 text-purple-700 border border-purple-200' :
                                  'bg-green-100 text-green-700 border border-green-200'
                                }`}>
                                  {endpoint.auth === 'Required' ? '🔒 Auth Required' :
                                   endpoint.auth === 'Optional' ? '🔓 Auth Optional' :
                                   endpoint.auth === 'Refresh Token' ? '🔄 Refresh Token' :
                                   '🌐 Public'}
                                </span>
                              </div>
                              <p className="text-gray-600">{endpoint.description}</p>
                            </div>
                            {isExpanded ? <ChevronDown className="w-5 h-5 text-gray-400" /> : <ChevronRight className="w-5 h-5 text-gray-400" />}
                          </div>
                        </button>

                        {isExpanded && (
                          <div className="px-6 pb-6 space-y-4 border-t border-gray-200 pt-4 bg-gray-50">
                            {endpoint.params && (
                              <div className="bg-white rounded-lg p-4 border border-gray-200">
                                <h4 className="text-sm font-semibold text-blue-600 mb-2">Query Parameters</h4>
                                <div className="space-y-1">
                                  {endpoint.params.map((param, i) => (
                                    <code key={i} className="text-sm text-gray-700 block">
                                      • {param}
                                    </code>
                                  ))}
                                </div>
                              </div>
                            )}

                            {endpoint.request && (
                              <div className="bg-white rounded-lg p-4 border border-gray-200">
                                <h4 className="text-sm font-semibold text-purple-600 mb-2">Request Body</h4>
                                <pre className="text-sm text-gray-700 overflow-x-auto">
                                  {JSON.stringify(endpoint.request, null, 2)}
                                </pre>
                              </div>
                            )}

                            {endpoint.response && (
                              <div className="bg-white rounded-lg p-4 border border-gray-200">
                                <h4 className="text-sm font-semibold text-green-600 mb-2">Response Type</h4>
                                <code className="text-sm text-gray-700">{endpoint.response}</code>
                              </div>
                            )}

                            {/* Test Section */}
                            <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
                              <button
                                onClick={() => toggleTesting(categoryIndex, endpointIndex)}
                                className="w-full px-4 py-3 flex items-center justify-between bg-blue-50 hover:bg-blue-100 transition-colors"
                              >
                                <div className="flex items-center gap-2">
                                  <Play className="w-4 h-4 text-blue-600" />
                                  <span className="font-semibold text-blue-600">Test Endpoint</span>
                                </div>
                                {isTesting ? <ChevronDown className="w-4 h-4 text-blue-600" /> : <ChevronRight className="w-4 h-4 text-blue-600" />}
                              </button>

                              {isTesting && (
                                <div className="p-4 space-y-4">
                                  {/* Auth Token Input */}
                                  {(endpoint.auth === 'Required' || endpoint.auth === 'Optional') && (
                                    <div>
                                      <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Access Token {endpoint.auth === 'Required' && <span className="text-red-500">*</span>}
                                      </label>
                                      <input
                                        type="text"
                                        placeholder="Enter access token"
                                        value={String(requestData[key]?.access_token || '')}
                                        onChange={(e) => updateRequestData(key, 'access_token', e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                      />
                                    </div>
                                  )}

                                  {/* Path Parameters */}
                                  {endpoint.params && endpoint.params.filter(p => !p.includes('?')).map((param) => (
                                    <div key={param}>
                                      <label className="block text-sm font-medium text-gray-700 mb-1">
                                        {param} <span className="text-red-500">*</span>
                                      </label>
                                      <input
                                        type="text"
                                        placeholder={`Enter ${param}`}
                                        value={String(requestData[key]?.[param] || '')}
                                        onChange={(e) => updateRequestData(key, param, e.target.value)}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                      />
                                    </div>
                                  ))}

                                  {/* Query Parameters */}
                                  {endpoint.params && endpoint.params.filter(p => p.includes('?')).map((param) => {
                                    const paramName = param.replace('?', '');
                                    return (
                                      <div key={param}>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                          {paramName} (optional)
                                        </label>
                                        <input
                                          type="text"
                                          placeholder={`Enter ${paramName}`}
                                          value={String(requestData[key]?.[paramName] || '')}
                                          onChange={(e) => updateRequestData(key, paramName, e.target.value)}
                                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        />
                                      </div>
                                    );
                                  })}

                                  {/* Request Body Fields */}
                                  {endpoint.request && Object.entries(endpoint.request).map(([field, type]) => {
                                    const isRequired = !type.includes('?');
                                    const isBoolean = type.includes('boolean');
                                    const isNumber = type.includes('integer');

                                    return (
                                      <div key={field}>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                          {field} {isRequired && <span className="text-red-500">*</span>}
                                          <span className="text-gray-500 text-xs ml-1">({type})</span>
                                        </label>
                                        {isBoolean ? (
                                          <select
                                            value={String(requestData[key]?.[field] || '')}
                                            onChange={(e) => updateRequestData(key, field, e.target.value === 'true')}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                          >
                                            <option value="">Select...</option>
                                            <option value="true">true</option>
                                            <option value="false">false</option>
                                          </select>
                                        ) : (
                                          <input
                                            type={isNumber ? 'number' : 'text'}
                                            placeholder={`Enter ${field}`}
                                            value={String(requestData[key]?.[field] || '')}
                                            onChange={(e) => updateRequestData(key, field, isNumber ? parseInt(e.target.value) || '' : e.target.value)}
                                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                                          />
                                        )}
                                      </div>
                                    );
                                  })}

                                  <button
                                    onClick={() => handleTest(categoryIndex, endpointIndex, endpoint)}
                                    disabled={isLoading}
                                    className="w-full bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 flex items-center justify-center gap-2"
                                  >
                                    {isLoading ? (
                                      <>
                                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                                        Testing...
                                      </>
                                    ) : (
                                      <>
                                        <Play className="w-4 h-4" />
                                        Send Request
                                      </>
                                    )}
                                  </button>

                                  {/* Response */}
                                  {response && (
                                    <div className="mt-4 bg-gray-900 rounded-lg p-4 text-white">
                                      <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                          <span className="text-sm font-semibold">Response</span>
                                          <span className={`text-xs px-2 py-1 rounded ${
                                            typeof response.status === 'number' && response.status >= 200 && response.status < 300
                                              ? 'bg-green-600'
                                              : typeof response.status === 'number' && response.status >= 400
                                              ? 'bg-red-600'
                                              : 'bg-yellow-600'
                                          }`}>
                                            {response.status} {response.statusText}
                                          </span>
                                        </div>
                                        <button
                                          onClick={() => copyResponse(key)}
                                          className="text-gray-400 hover:text-white transition-colors"
                                          title="Copy response"
                                        >
                                          {copiedResponse === key ? (
                                            <Check className="w-4 h-4 text-green-400" />
                                          ) : (
                                            <Copy className="w-4 h-4" />
                                          )}
                                        </button>
                                      </div>
                                      <pre className="text-sm overflow-x-auto">
                                        {JSON.stringify(response.data, null, 2)}
                                      </pre>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>

        {filteredRoutes.length === 0 && (
          <div className="text-center py-16">
            <Search className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-600 text-lg">No routes found matching your search</p>
          </div>
        )}

        {/* Footer */}
        <div className="mt-12 text-center text-gray-500 text-sm pb-8">
          <p>TzHar URL Shortener API v1.0.0</p>
          <p className="mt-2">Built with FastAPI • OpenAPI 3.1.0</p>
        </div>
      </div>
    </div>
  );
};

export default APIRoutesExplorer;