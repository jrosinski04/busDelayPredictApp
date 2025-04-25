import React, { useState, useRef, useEffect } from "react";
import { View, Text, Pressable, StyleSheet } from 'react-native';

const StopDropdown = ({ stops = [], onSelectStop }) => {
    const [query, setQuery] = useState("");
    const [isOpen, setIsOpen] = useState(false);
    const [hoverStates, setHoverStates] = useState({});
    const dropdownRef = useRef(null);

    const handleHover = (index, value) => {
        setHoverStates(prev => ({ ...prev, [index]: value }));
    };

    const filteredStops = stops.filter(stop =>
        stop.toLowerCase().includes(query.toLowerCase())
    );

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    return (
        <div ref={dropdownRef} style={styles.dropdownContainer}>
            <input
                type="text"
                placeholder="Search for bus stop"
                value={query}
                onFocus={() => setIsOpen(true)}
                onChange={(e) => setQuery(e.target.value)}
                style={{
                    display: "block",
                    padding: "0.8rem",
                    margin: "0.6rem",
                    borderRadius: "0.25rem",
                    borderWidth: "1px"
                }}
            />
            {isOpen && (
                <div style={styles.dropdown}>
                    {filteredStops.map((stop, index) => (
                        <Pressable
                            key={index}
                            style={{
                                ...styles.listItem,
                                ...(hoverStates[index] ? styles.hoveredItem : {})
                            }}
                            onPressIn={() => handleHover(index, true)}
                            onPressOut={() => handleHover(index, false)}
                            onPress={() => {
                                onSelectStop(stop);
                                setQuery(stop); // Optional: set input to selected stop
                                setIsOpen(false);
                            }}
                        >
                            <Text>{stop}</Text>
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
        backgroundColor: 'orange',
    },
    hoveredItem: {
        backgroundColor: 'black',
    },
    dropdownContainer: {
        position: 'relative',
        width: '100%',
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

export default StopDropdown;
