import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TextInput,
  Pressable,
  StyleSheet,
  Keyboard,
} from "react-native";
import DateTimePickerModal from "react-native-modal-datetime-picker";
import axios from "axios";
import Dropdown from "@/components/Dropdown";

const MainPage = () => {
  const [servicesList, setServicesList] = useState([]);
  const [selectedService, setSelectedService] = useState("");
  const [stopsList, setStopsList] = useState<string[]>([]);
  const [departureDate, setDepartureDate] = useState(new Date());
  const [departureTime, setDepartureTime] = useState("");
  const [departureStop, setDepartureStop] = useState("");
  const [isDatePickerVisible, setDatePickerVisibility] = useState(false);
  const [predictedDelay, setPredictedDelay] = useState(null);
  const [origin, setOrigin] = useState("");
  const [originalOrigin, setOriginalOrigin] = useState("");
  const [destination, setDestination] = useState("");
  const [originalDestination, setOriginalDestination] = useState("")
  const [showDirectionOptions, setShowDirectionOptions] = useState(false);

  useEffect(() => {
    const fetchServices = async () => {
      try {
        const response = await axios.get(
          "https://fetchbusservices.onrender.com/get_services",
          { params: { query: "" } }
        );
        setServicesList(response.data);
      } catch (error) {
        console.error("Error fetching services: ", error);
      }
    };
    fetchServices();
  }, []);

  useEffect(() => {
    const isReady =
      typeof selectedService === 'string' && selectedService.length > 0 &&
      typeof departureStop === 'string' && departureStop.length > 0 &&
      departureDate instanceof Date &&
      typeof departureTime === 'string' && departureTime.length > 0 &&
      typeof destination === 'string' && destination.length > 0;

    if (isReady) {
      predictDelay();
    }
  }, [selectedService, departureStop, departureDate, departureTime, destination]);

  const showDatePicker = () => setDatePickerVisibility(true);
  const hideDatePicker = () => setDatePickerVisibility(false);

  const handleDateConfirm = (date) => {
    setDepartureDate(date);
    hideDatePicker();
  };

  const handleServiceSelect = async (selectedLabel) => {
    const selected = servicesList.find(
      (s) => `${s.number}: ${s.description}` === selectedLabel
    );
    if (!selected) return;

    setSelectedService(selectedLabel);
    setDepartureStop("");

    try {
      const response = await axios.get(
        "https://fetchbusservices.onrender.com/get_stops",
        { params: { service_id: selected._id } }
      );
      setStopsList(response.data);

      setOriginalOrigin(stopsList[0]);
      setOriginalDestination(stopsList[stopsList.length - 1]);
      setOrigin(originalOrigin);
      setDestination(originalDestination);
    } catch (error) {
      console.error("Error fetching stops: ", error);
    }
  };

  const handleStopSelect = (stop) => {
    setDepartureStop(stop);
  };

  const predictDelay = async () => {
    try {
      const selected = servicesList.find(
        (s) => `${s.number}: ${s.description}` === selectedService
      );
      if (!selected) return;

      const params = {
        service_id: parseInt(selected._id),
        stop_name: departureStop,
        destination: destination,
        date: departureDate.toISOString().split("T")[0],
        time: departureTime,
      };
      console.log(params)
      const response = await axios.post(
        "https://fetchbusservices.onrender.com/predict_delay",
        params,
        {
          headers: { "Content-Type": "application/json" }
        }
      );

      setPredictedDelay(response.data.delay);
    } catch (error) {
      console.error("Prediction error:", error);
    }
  };

  const sortedServiceLabels = [...servicesList]
    .sort((a, b) => parseInt(a.number) - parseInt(b.number))
    .map((s) => `${s.number}: ${s.description}`);

  return (
    <View style={{ padding: 16, marginTop: 50 }}>
      {/* Date Picker */}
      <Pressable onPress={showDatePicker}>
        <TextInput
          placeholder="Departure date"
          value={departureDate.toISOString().split("T")[0]}
          editable={false}
          style={styles.inputBox}
        />
      </Pressable>
      <DateTimePickerModal
        isVisible={isDatePickerVisible}
        mode="date"
        date={departureDate}
        onConfirm={handleDateConfirm}
        onCancel={hideDatePicker}
      />

      {/* Time Input */}
      <TextInput
        placeholder="Departure time (HH:MM)"
        value={departureTime}
        onChangeText={setDepartureTime}
        style={styles.inputBox}
      />

      {/* Dropdowns */}
      <Dropdown
        data={sortedServiceLabels}
        placeholder="Search for service"
        onSelect={handleServiceSelect}
        value={selectedService}
      />
      <Dropdown
        data={stopsList}
        placeholder="Search for stop"
        onSelect={handleStopSelect}
        value={departureStop}
      />

      {!showDirectionOptions && selectedService && departureStop && departureDate && departureTime && (
        <Pressable
          onPress={() => setShowDirectionOptions(true)}
          style={styles.continueButton}
        >
          <Text style={styles.continueButtonText}>Continue</Text>
        </Pressable>
      )}


      {showDirectionOptions && (
        <View style={styles.directionContainer}>
          <Text style={styles.label}>Choose direction of travel:</Text>
          <Pressable
            onPress={() => setDestination(stopsList[stopsList.length - 1])}
            style={styles.directionButton}
          >
            <Text>{stopsList[0]} → {stopsList[stopsList.length - 1]}</Text>
          </Pressable>
          <Pressable
            onPress={() => setDestination(stopsList[0])}
            style={styles.directionButton}
          >
            <Text>{stopsList[stopsList.length - 1]} → {stopsList[0]}</Text>
          </Pressable>
        </View>
      )}


      {/* Display Selections */}
      <View style={styles.infoSection}>
        <Text style={styles.infoTitle}>Selected Service</Text>
        <Text>{selectedService}</Text>
        <Text style={styles.infoTitle}>Selected Stop</Text>
        <Text>{departureStop}</Text>
        <Text style={styles.infoTitle}>Direction</Text>
        <Text>{destination}</Text>
        {predictedDelay !== null && (
          <View style={styles.resultBox}>
            <Text style={styles.infoTitle}>Predicted Delay:</Text>
            <Text>{predictedDelay} minutes</Text>
          </View>
        )}
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  inputBox: {
    padding: 10,
    marginBottom: 10,
    borderRadius: 5,
    borderWidth: 1,
    backgroundColor: "white",
  },
  infoSection: {
    marginTop: 20,
    padding: 10,
    borderWidth: 1,
    borderRadius: 5,
  },
  infoTitle: {
    fontWeight: "bold",
    fontSize: 16,
    marginBottom: 4,
  },
  resultBox: {
    marginTop: 10,
    padding: 10,
    backgroundColor: "#f0f8ff",
    borderRadius: 5,
  },
  directionContainer: {
    marginTop: 20,
    marginBottom: 10,
  },
  button: {
    padding: 10,
    marginVertical: 4,
    borderWidth: 1,
    borderRadius: 5,
  },
  continueButton: {
    backgroundColor: "#007AFF",
    padding: 12,
    borderRadius: 6,
    alignItems: "center",
    marginTop: 10,
  },
  continueButtonText: {
    color: "white",
    fontWeight: "bold",
  },
  directionButton: {
    padding: 10,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 6,
    marginTop: 6,
    backgroundColor: "#f5f5f5",
  },
  label: {
    fontWeight: "bold",
    marginBottom: 6,
  }

});

export default MainPage;
