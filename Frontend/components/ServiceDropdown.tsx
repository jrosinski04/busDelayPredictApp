import React, { useState, useEffect, useRef } from "react";
import { View, Text, Pressable, StyleSheet } from 'react-native';
import axios from "axios";

const ServiceDropdown = ({ onSelectService }) => {
    const [services, setServices] = useState([]);
    const [query, setQuery] = useState("");
    const [hoverStates, setHoverStates] = React.useState({});
    const [isOpen, setIsOpen] = useState(false);
    const [search, setSearch] = useState("");
    const dropdownRef = useRef(null);

    const handleHover = (index, value) => {
        setHoverStates(prev => ({ ...prev, [index]: value }));
    };

    useEffect(() => {
        if (query.length > 0) {
            fetchServices(query);
        }
    }, [query]);

    // Close dropdown menu when search box is deselected
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
    }, []);

    const fetchServices = async (query) => {
        try {
            const response = await axios.get(
                'https://fetchbusservices.onrender.com/get_services', { params: {query: query }, }
            );
            console.log("Response status: ", response.status);
            console.log("Response data: ", response.data);
            setServices(response.data);
            console.log(services);
        } catch (error) {
            console.error("Error fetching services: ", error);
        }
    };

    return (
        <div ref={dropdownRef} style={{position: 'relative', width: '100%'}}>
            <input
                type="text"
                placeholder="Search for route"
                value={query}
                onFocus={() => setIsOpen(true)}
                onChange={(e) => setQuery(e.target.value)}
                style={{"display":"block","padding":"0.8rem","margin":"0.6rem","borderRadius":"0.25rem","borderWidth":"1px"}}
            />
            {isOpen && (
                <div style={styles.dropdown}>
                {services.map((service, index) => (
                    <Pressable
                        key={service._id}
                        style={{
                            ...styles.listItem, 
                            ...(hoverStates[index] ? styles.hoveredItem : {})
                        }}
                        onPressIn={() => handleHover(index, true)}
                        onPressOut={() => handleHover(index, false)}
                        onPress={() => { onSelectService(service); setIsOpen(false);}}
                    >
                        <Text>{service.Service}: {service.Origin} + {service.Destination}</Text>
                    </Pressable>
                ))}
                </div>
            )}
            
        </div>
    );
};

const styles = StyleSheet.create({
    listItem: {
        padding: 2,
        borderStyle: 'solid',
        borderColor: 'gray',
        borderWidth: 1,
        backgroundColor: 'orange'
    },
    hoveredItem: {
        backgroundColor: 'black'
    },
    dropdownContainer: {
        position: 'relative',
        width: '100%'
    },
    dropdown: {
        position: 'absolute',
        width: '100%',
        maxHeight: 200,
        overflowY: 'auto',
        backgroundColor: 'white',
        borderColor: '#ccc',
        borderStyle: 'solid',
        borderRadius: 4,
        boxShadow: '0px 4px 6px rgba(0,0,0,0.1)',
        zIndex: 1000,
    },
});

export default ServiceDropdown;