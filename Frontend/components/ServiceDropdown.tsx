import React, { useState, useEffect, useRef } from "react";
import { View, Text, Pressable, StyleSheet, TextInput, FlatList, TouchableWithoutFeedback, Keyboard } from 'react-native';
import axios from "axios";

const ServiceDropdown = ({ onSelectService }) => {
    const [services, setServices] = useState([]);
    const [query, setQuery] = useState("");
    const [isOpen, setIsOpen] = useState(false);

    const fetchServices = async (query) => {
        try {
            const response = await axios.get(
                "https://fetchbusservices.onrender.com/get_services",
                { params: { query } }
            );
            setServices(response.data);
        } catch (error) {
            console.error("Error fetching services: ", error);
        }
    };

    const handleSelect = (service) => {
        onSelectService(service);
        setIsOpen(false);
        setQuery(""); // Optional: clear input
        Keyboard.dismiss();
    };

    return (
            <View style={styles.dropdownContainer}>
                <TextInput
                    placeholder="Search for route"
                    value={query}
                    onFocus={() => {
                        setIsOpen(true)
                        fetchServices("");
                    }}
                    onChangeText={(text) => {
                        setQuery(text);
                        fetchServices(text);
                    }}
                    onTouchEnd={() => {
                        setIsOpen(false)
                    }}
                    style={styles.inputBox}
                />

                {isOpen && services.length > 0 && (
                    <View style={styles.dropdown}>
                        <FlatList
                            data={services}
                            keyExtractor={(item) => item._id}
                            renderItem={({ item }) => (
                                <Pressable
                                    onPress={() => handleSelect(item)}
                                    style={({ pressed }) => [
                                        styles.listItem,
                                        pressed && styles.pressedItem,
                                    ]}
                                >
                                    <Text>
                                        {item.number}: {item.description}
                                    </Text>
                                </Pressable>
                            )}
                        />
                    </View>
                )}
            </View>
    );
};

const styles = StyleSheet.create({
    listItem: {
        padding: 2,
        borderStyle: 'solid',
        borderColor: 'grey',
        borderWidth: 1,
        backgroundColor: 'grey'
    },
    hoveredItem: {
        backgroundColor: 'black'
    },
    dropdownContainer: {
        position: 'relative',
        width: '100%',
    },
    dropdown: {
        position: 'absolute',
        marginTop: 50,
        width: '100%',
        maxHeight: 200,
        overflowY: 'auto',
        borderColor: '#ccc',
        borderStyle: 'solid',
        borderRadius: 4,
        boxShadow: '0px 4px 6px rgba(0,0,0,0.1)',
        zIndex: 1000,
    },
    inputBox: {
        padding: 10,
        margin: 8,
        borderRadius: 5,
        borderWidth: 1
    },
});

export default ServiceDropdown;